# SonarQube Community on Kubernetes

[![Validate](https://github.com/imos64/sonarqube-kubernetes/actions/workflows/validate.yaml/badge.svg)](https://github.com/imos64/sonarqube-kubernetes/actions/workflows/validate.yaml)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.34-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Helm](https://img.shields.io/badge/Helm-3-0F1689?logo=helm)](https://helm.sh/)
[![Terraform](https://img.shields.io/badge/Terraform-supported-7B42BC?logo=terraform)](terraform/)
[![OpenTofu](https://img.shields.io/badge/OpenTofu-supported-FFDA18?logo=opentofu)](opentofu/)

Maintained by [imos64](https://github.com/imos64). A public deployment package with pinned sources, native Kubernetes manifests, Helm, Terraform and OpenTofu, architecture documentation, and recovery runbooks. It follows the structure of [prometheus-kubernetes](https://github.com/imos64/prometheus-kubernetes/tree/main).

## Architecture

One SonarQube Community application uses a persistent data volume and an external PostgreSQL database. Pair it with the PostgreSQL HA repository; database HA does not make the Community application active-active.

```mermaid
flowchart LR
Scanner --> Sonar[SonarQube Community]
Sonar --> Index[Search index PVC]
Sonar --> PG[External PostgreSQL HA]
PG --> Backup[Encrypted database backups]
```

Community supports one application instance. Do not increase replicas or share the embedded search data directory. Multi-node SonarQube requires the supported Data Center edition and a separate licensed architecture.

## Delivery paths

| Path | Purpose |
| --- | --- |
| `charts/sonarqube` | Local Helm chart and base/production values |
| `k8s/base`, `k8s/production` | Reproducible rendered manifests with Kustomize entry points |
| `terraform`, `opentofu` | Alternative Helm release owners on an existing Kubernetes cluster |
| `scripts` | Rendering, schema validation, secret-reference and topology checks |
| `docs` | Architecture, configuration, operations, validation and source provenance |
| `examples` | Deployment-specific integration and recovery examples |

Use **one** delivery path per release. These modules deploy applications to an existing cluster; they do not provision cloud networks, worker nodes, DNS, object storage or a CSI driver. Base is smaller for evaluation, while production increases storage/resources and supported replicas. Neither profile configures your organization's backup destination or proves an availability SLO.

## Prerequisites

- Kubernetes 1.34-compatible APIs, Helm 3, and a working default RWO StorageClass for stateful workloads. Plan storage expansion and volume reattachment; node-local storage cannot survive permanent node loss.
- For three-member clusters, three schedulable workers in appropriate fault domains. Set node/zone placement and storage topology for your environment.
- A CNI that enforces NetworkPolicy. Workload ingress permits this namespace and namespaces explicitly labeled `platform-access=true`; egress is not restricted by the supplied policy. Internal HTTP services need TLS/authentication at your approved access boundary.
- An explicit kubeconfig/context and namespace access. Operator installation additionally requires cluster-scoped CRD/RBAC privileges.
- Existing credentials delivered by your secret manager. No real passwords, certificates, state files or private project configurations are committed.

Create the `sonarqube` PostgreSQL database and role with the same password as `sonarqube-jdbc`. Permit namespace `sonarqube` to reach PostgreSQL with the `platform-access=true` label. Set node `vm.max_map_count>=524288`, `fs.file-max>=131072`, and process file/thread limits per SonarSource requirements; privileged sysctl init containers are deliberately disabled. Rotate the initial built-in admin password before exposure.

## Quick start

```bash
git clone https://github.com/imos64/sonarqube-kubernetes.git
cd sonarqube-kubernetes
export KUBECONFIG=/absolute/path/to/your/kubeconfig
kubectl config current-context
kubectl create namespace sonarqube
```

Review [configuration and credentials](docs/configuration.md) before installation. `scripts/bootstrap-demo-secrets.py` generates fresh credentials directly in the selected cluster for a disposable evaluation; it refuses to overwrite an existing secret and never prints generated passwords. For production, provision the same keys using your secret-management workflow.

```bash
python3 scripts/bootstrap-demo-secrets.py --context YOUR_CONTEXT
```

### Helm

```bash
helm upgrade --install sonarqube ./charts/sonarqube -n sonarqube \
  -f charts/sonarqube/values-production.yaml --wait --timeout 15m
```

Add `-f /secure/path/site-values.yaml` last for your storage class, sizing and integrations. Helm's release wait does not prove database quorum or custom-resource readiness; run the acceptance checks below.

### Native Kubernetes

```bash
kubectl apply --server-side -k k8s/production
```

For customized native manifests, edit chart values then run `make render` and review the diff. The rendered namespace/release defaults are `sonarqube`; re-render intentionally if you change that contract. Helm hook Jobs become ordinary Jobs under kubectl, so check their completion and delete only completed setup Jobs before rerunning changed hooks.

### Terraform or OpenTofu

Both modules use the same pinned local Helm source. They require the namespace and secrets to exist first. Keep state in an encrypted remote backend with locking; state and plans can contain sensitive information.

```bash
terraform -chdir=terraform init
terraform -chdir=terraform plan -var='kube_context=YOUR_CONTEXT' -out=deployment.tfplan
terraform -chdir=terraform apply deployment.tfplan
# OR
 tofu -chdir=opentofu init
 tofu -chdir=opentofu plan -var='kube_context=YOUR_CONTEXT' -out=deployment.tfplan
 tofu -chdir=opentofu apply deployment.tfplan
```

Use `kubeconfig_path` and `values_files` to supply your environment. See `deployment.tfvars.example`. Never manage the same release from Terraform and OpenTofu simultaneously. 

## Access and acceptance

Internal endpoint: **`sonarqube.sonarqube.svc.cluster.local:9000`**.

Wait for the application rollout and `/api/system/status` to report UP. Authenticate, scan a small test project, verify its quality gate, restart the pod, and confirm project history persists. A healthy PostgreSQL pod alone is insufficient.

## Operations and recovery

PostgreSQL is the authoritative application state. Schedule database backups and retain extension/plugin versions and configuration. Restore PostgreSQL first, start the matching SonarQube version in isolation, let search indexes rebuild, and validate project history, users and quality gates. Coordinate DB migration rollback with a pre-upgrade backup.

See [operations](docs/operations.md) for backup, restore, upgrade and failure checks. HA replication is not a backup. Retained PVCs do not protect against storage-system failure, accidental deletion or site loss.

## Validation

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python3 scripts/install-tools.py
export PATH="$PWD/.tools:$PATH"
make render
make validate
```

CI checks deterministic rendering, strict Helm lint, Kubernetes and custom-resource schemas, topology/secret contracts, Terraform/OpenTofu validation and secret scanning. Runtime acceptance and disaster-recovery steps are documented separately in [validation evidence](docs/validation.md); configuration validation is not proof of production readiness.

## Sources and license

This repository owns the integration/deployment code, not the upstream application. [Upstream project](https://github.com/SonarSource/helm-chart-sonarqube) · [Official documentation](https://docs.sonarsource.com/sonarqube-community-build/setup-and-upgrade/deploy-on-kubernetes/). See [provenance](docs/provenance.md) for pinned versions and SHA-256 chart checksums. Deployment code is Apache-2.0; bundled upstream charts, schemas and container images retain their original licenses. Review application licensing for your use case, especially Nexus, SonarQube, Redis and MongoDB-derived distributions.
