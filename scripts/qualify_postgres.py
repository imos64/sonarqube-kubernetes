#!/usr/bin/env python3
"""Build, scan and test the exact committed PostgreSQL candidate; never publish."""
import argparse
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TRIVY_URL = 'https://github.com/aquasecurity/trivy/releases/download/v0.74.0/trivy_0.74.0_Linux-64bit.tar.gz'
TRIVY_SHA = '2ae6fe3ee734b7fdf11335663e18c75ea12dccc76062f09f164a3b0f8be4371a'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(command, log):
    with log.open('wb') as stream:
        return subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    receipt = {'schema_version': 1, 'source_repository': 'https://github.com/imos64/sonarqube-kubernetes',
               'source_revision': revision, 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'run_id': os.getenv('GITHUB_RUN_ID'), 'run_attempt': os.getenv('GITHUB_RUN_ATTEMPT'),
               'event': os.getenv('GITHUB_EVENT_NAME'), 'passed': False, 'published': False,
               'deploy_allowed': False, 'durably_accepted': False}
    try:
        context = ROOT / 'runtime/postgres'
        paths = [p for p in context.rglob('*') if p.is_file()]
        paths += [Path(__file__).resolve(), ROOT / '.github/workflows/validate.yaml']
        inventory = {}
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            committed = subprocess.check_output(['git', 'show', revision + ':' + relative], cwd=ROOT)
            require(path.read_bytes() == committed, 'uncommitted qualification input: ' + relative)
            inventory[relative] = sha(committed)
        receipt['input_sha256'] = inventory
        lock = json.loads((context / 'sources.lock.json').read_bytes())
        require(sha((context / 'gosu-source.tar').read_bytes()) == lock['gosu_archive_sha256'], 'gosu source mismatch')
        tag = 'local/sonar-postgres:' + revision
        receipt['image'] = tag
        require(run(['docker', 'build', '--progress=plain', '--build-arg', 'SOURCE_REVISION=' + revision,
                     '-t', tag, str(context)], out / 'build.log') == 0, 'build failed')
        image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', tag]))[0]
        require(image['Config']['User'] == '70:70', 'runtime identity changed')
        require(image['Config']['Labels']['org.opencontainers.image.revision'] == revision, 'source revision mismatch')
        require(image['Config']['Labels']['org.opencontainers.image.source'] == receipt['source_repository'], 'source repository mismatch')
        receipt['docker_image_id'] = image['Id']
        receipt['diff_ids'] = image['RootFS']['Layers']
        with tempfile.TemporaryDirectory(prefix='postgres-image-scan-') as private:
            private = Path(private)
            raw = urllib.request.urlopen(TRIVY_URL, timeout=90).read()
            require(sha(raw) == TRIVY_SHA, 'scanner archive mismatch')
            with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
                (private / 'trivy').write_bytes(archive.extractfile('trivy').read())
            binary = private / 'trivy'
            binary.chmod(0o755)
            (private / 'empty.ignore').write_text('')
            (private / 'empty.yaml').write_text('{}\n')
            require(run(['docker', 'save', '--output', str(private / 'image.tar'), tag], out / 'export.log') == 0,
                    'image export failed')
            receipt['local_docker_archive_sha256'] = sha((private / 'image.tar').read_bytes())
            common = [str(binary), 'image', '--input', str(private / 'image.tar'),
                      '--config', str(private / 'empty.yaml'), '--ignorefile', str(private / 'empty.ignore'),
                      '--secret-config', str(private / 'empty.yaml'), '--timeout', '15m',
                      '--cache-dir', str(ROOT / '.runtime-cache')]
            receipt['scan_exit_code'] = run(common + ['--scanners', 'vuln,secret', '--severity', 'HIGH,CRITICAL',
                '--ignore-unfixed=false', '--list-all-pkgs', '--exit-code', '1', '--format', 'json',
                '--output', str(out / 'image.json')], out / 'scan.log')
            receipt['sbom_exit_code'] = run(common + ['--format', 'cyclonedx', '--output', str(out / 'sbom.json')], out / 'sbom.log')
            receipt['scanner'] = json.loads(subprocess.check_output([str(binary), '--cache-dir',
                str(ROOT / '.runtime-cache'), '--version', '--format', 'json']))
            database = ROOT / '.runtime-cache/db/trivy.db'
            receipt['vulnerability_db_sha256'] = sha(database.read_bytes())
            require(receipt['scan_exit_code'] == receipt['sbom_exit_code'] == 0, 'scan/SBOM gate failed')
            scan = json.loads((out / 'image.json').read_bytes())
            require(scan['Metadata']['DiffIDs'] == receipt['diff_ids'], 'scan/image layer mismatch')
            require(scan['Metadata']['OS']['Family'] == 'alpine', 'missing OS inventory')
            require(all(not r.get('Vulnerabilities') and not r.get('Secrets') for r in scan['Results']), 'findings present')
            gosu = [r for r in scan['Results'] if r.get('Target') == 'usr/local/bin/gosu']
            require(len(gosu) == 1 and any(p['Name'] == 'stdlib' and p['Version'] == 'v1.27.1'
                    for p in gosu[0]['Packages']), 'compiled Go inventory missing or wrong version')
            sbom = json.loads((out / 'sbom.json').read_bytes())
            require(sbom.get('bomFormat') == 'CycloneDX' and len(sbom.get('components', [])) >= 45, 'incomplete SBOM')
        receipt['runtime_exit_code'] = run(['python3', str(context / 'qualify.py'), '--image', tag,
                                           '--output', str(out / 'runtime')], out / 'runtime.log')
        require(receipt['runtime_exit_code'] == 0, 'restricted runtime/backup qualification failed')
        receipt['passed'] = True
    finally:
        receipt['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt['files_sha256'] = {p.relative_to(out).as_posix(): sha(p.read_bytes()) for p in sorted(out.rglob('*'))
                                   if p.is_file() and p != out / 'receipt.json'}
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
