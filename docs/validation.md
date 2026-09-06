# Validation evidence and acceptance limits

The repository validation pipeline runs on every main-branch push and pull request. Its badge links to the actual run; inspect the commit and job result rather than assuming the badge proves runtime behavior.

## Automated checks

- Base and production Helm rendering, locked chart dependencies and deterministic committed native manifests.
- Strict Helm lint; core Kubernetes 1.34 schemas; CRD object schemas derived from Kubernetes v1.34.0 OpenAPI; custom resources validated against the supplied operator CRDs.
- Secret-reference, image-tag and HA topology contracts.
- Terraform and OpenTofu formatting, provider initialization and configuration validation.
- Gitleaks scans with only narrow Helm checksum-annotation false-positive exclusions.

These checks do not establish application readiness, workload capacity, node/zone failure tolerance, security certification or backup recoverability. The production profile is an integration baseline requiring site configuration and acceptance.

## Runtime acceptance

Wait for the application rollout and `/api/system/status` to report UP. Authenticate, scan a small test project, verify its quality gate, restart the pod, and confirm project history persists. A healthy PostgreSQL pod alone is insufficient.

See [operations](operations.md) for the separate restore drill. Runtime checks performed during repository creation, if any, are recorded in `runtime-evidence.md`. Absence of that file means runtime acceptance has not been executed for this package.
