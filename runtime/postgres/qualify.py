#!/usr/bin/env python3
"""Qualify one local image in disposable, network-isolated PostgreSQL containers.

Does not contact Kubernetes. Backup/restore here is a local fixture test, not
Sonar database acceptance or proof of an independent backup target.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=True)
    identity = json.loads(run(["docker", "image", "inspect", args.image]))[0]["Id"]
    suffix = secrets.token_hex(6)
    containers, volumes = [], []
    receipt = {"image": args.image, "local_image_id": identity,
               "durably_accepted": False, "scope": "isolated local fixture", "status": "failed", "checks": {}}
    password = secrets.token_urlsafe(40)

    def sql(container, statement, database="postgres"):
        return run(["docker", "exec", "-i", container, "psql", "-X", "-v",
                    "ON_ERROR_STOP=1", "-U", "postgres", "-d", database, "-At"],
                   input=statement.encode()).decode().strip()

    def wait_ready(container):
        for _ in range(60):
            result = subprocess.run(["docker", "exec", container, "pg_isready", "-U", "postgres"],
                                    capture_output=True)
            if result.returncode == 0:
                return
            time.sleep(1)
        raise RuntimeError("PostgreSQL readiness timeout")

    try:
        with tempfile.TemporaryDirectory(prefix="sonar-pg-qualification-") as private:
            env = Path(private) / "env"
            env.write_text("POSTGRES_PASSWORD=" + password +
                           "\nPOSTGRES_INITDB_ARGS=--auth-host=scram-sha-256\n")
            for side in ["source", "restore"]:
                name = "phasea-sonar-pg-" + suffix + "-" + side
                volume = name + "-data"
                run(["docker", "volume", "create", "--label", "purpose=sonar-image-qualification", volume])
                volumes.append(volume)
                # Docker lacks Kubernetes fsGroup. Initialize only this new disposable volume.
                run(["docker", "run", "--rm", "--user", "0:0", "--network", "none", "--read-only",
                     "--cap-drop", "ALL", "--cap-add", "CHOWN", "--security-opt", "no-new-privileges",
                     "--mount", "type=volume,src=" + volume + ",dst=/var/lib/postgresql/data",
                     "--entrypoint", "chown", identity, "70:70", "/var/lib/postgresql/data"])
                run(["docker", "run", "-d", "--name", name, "--network", "none",
                     "--user", "70:70", "--read-only", "--cap-drop", "ALL",
                     "--security-opt", "no-new-privileges", "--memory", "1g", "--cpus", "1",
                     "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m,uid=70,gid=70",
                     "--tmpfs", "/var/run/postgresql:rw,nosuid,nodev,size=16m,uid=70,gid=70",
                     "--mount", "type=volume,src=" + volume + ",dst=/var/lib/postgresql/data",
                     "--env-file", str(env), identity])
                containers.append(name)
                wait_ready(name)
                sql(name, "CREATE DATABASE qualification;")
            source, restored = containers
            receipt["server_version"] = sql(source, "SHOW server_version;")
            receipt["checks"]["restricted_initialization"] = True
            bad = subprocess.run(["docker", "exec", "-e", "PGPASSWORD=deliberately-wrong", source,
                                  "psql", "-h", "127.0.0.1", "-U", "postgres", "-Atc", "SELECT 1"],
                                 capture_output=True)
            assert bad.returncode != 0 and b"password authentication failed" in bad.stderr
            good = run(["docker", "exec", source, "sh", "-c",
                        'PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U postgres -Atc "SELECT 1"'])
            assert good.strip() == b"1"
            receipt["checks"]["password_authentication"] = True
            sql(source, "CREATE TABLE sample(id integer PRIMARY KEY, body text NOT NULL); "
                "INSERT INTO sample SELECT i, repeat(md5(i::text),32) FROM generate_series(1,10000) i;",
                "qualification")
            query = "SELECT count(*)::text || ':' || md5(string_agg(id::text||body, ',' ORDER BY id)) FROM sample;"
            before = sql(source, query, "qualification")
            run(["docker", "restart", source])
            wait_ready(source)
            assert sql(source, query, "qualification") == before
            receipt["checks"]["persistence_after_restart"] = True
            dump = run(["docker", "exec", source, "pg_dump", "-U", "postgres", "-Fc", "qualification"])
            (args.output / "fixture.dump").write_bytes(dump)
            run(["docker", "exec", "-i", restored, "pg_restore", "-U", "postgres", "--exit-on-error",
                 "--no-owner", "--dbname=qualification"], input=dump)
            assert sql(restored, query, "qualification") == before
            receipt["checks"]["restore_to_separate_container_and_volume"] = True
            receipt["rows_and_content_fingerprint"] = before
            receipt["backup_sha256"] = hashlib.sha256(dump).hexdigest()
            receipt["status"] = "passed"
    finally:
        for name in containers:
            logs = subprocess.run(["docker", "logs", name], capture_output=True, text=True)
            (args.output / (name.rsplit('-', 1)[-1] + '.log')).write_text(
                (logs.stdout + logs.stderr).replace(password, '[REDACTED]'))
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=True)
        for volume in volumes:
            subprocess.run(["docker", "volume", "rm", volume], capture_output=True, check=True)
        (args.output / "qualification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
