#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
helm lint charts/sonarqube --strict
helm lint charts/sonarqube --strict -f charts/sonarqube/values-production.yaml
python3 scripts/check_manifests.py
python3 scripts/check_topology.py
python3 scripts/check_digest_image.py
terraform -chdir=terraform fmt -check
terraform -chdir=terraform init -backend=false -input=false
terraform -chdir=terraform validate
tofu -chdir=opentofu fmt -check
tofu -chdir=opentofu init -backend=false -input=false
tofu -chdir=opentofu validate
gitleaks dir . --redact --no-banner
