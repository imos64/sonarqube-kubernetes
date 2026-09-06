#!/usr/bin/env python3
"""Install pinned Linux x86_64 validation tools after SHA-256 verification."""
from pathlib import Path
import hashlib
import io
import tarfile
import urllib.request
import zipfile

out = Path(__file__).resolve().parents[1] / ".tools"
out.mkdir(exist_ok=True)
# URL, checksum URL, archive member/binary name.
specs = [
    ("https://get.helm.sh/helm-v3.21.3-linux-amd64.tar.gz", "https://get.helm.sh/helm-v3.21.3-linux-amd64.tar.gz.sha256sum", "helm"),
    ("https://releases.hashicorp.com/terraform/1.15.8/terraform_1.15.8_linux_amd64.zip", "https://releases.hashicorp.com/terraform/1.15.8/terraform_1.15.8_SHA256SUMS", "terraform"),
    ("https://github.com/opentofu/opentofu/releases/download/v1.12.6/tofu_1.12.6_linux_amd64.tar.gz", "https://github.com/opentofu/opentofu/releases/download/v1.12.6/tofu_1.12.6_SHA256SUMS", "tofu"),
    ("https://github.com/yannh/kubeconform/releases/download/v0.8.0/kubeconform-linux-amd64.tar.gz", "https://github.com/yannh/kubeconform/releases/download/v0.8.0/CHECKSUMS", "kubeconform"),
    ("https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz", "https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_checksums.txt", "gitleaks"),
    ("https://dl.k8s.io/release/v1.34.0/bin/linux/amd64/kubectl", "https://dl.k8s.io/release/v1.34.0/bin/linux/amd64/kubectl.sha256", "kubectl"),
]
for url, sums_url, binary in specs:
    data = urllib.request.urlopen(url, timeout=120).read()
    sums = urllib.request.urlopen(sums_url, timeout=120).read().decode()
    digest = hashlib.sha256(data).hexdigest()
    filename = url.rsplit("/", 1)[1]
    assert any(line.split()[0] == digest and (len(line.split()) == 1 or line.split()[-1].lstrip("*") == filename) for line in sums.splitlines()), binary
    if url.endswith(".tar.gz"):
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            member = next(m for m in archive.getmembers() if m.isfile() and m.name.rsplit("/", 1)[-1] == binary)
            payload = archive.extractfile(member).read()
    elif url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            payload = archive.read(binary)
    else:
        payload = data
    (out / binary).write_bytes(payload)
    (out / binary).chmod(0o755)
    print("Installed checksum-verified", binary)
