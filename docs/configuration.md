# Configuration

Create the `sonarqube` PostgreSQL database and role with the same password as `sonarqube-jdbc`. Permit namespace `sonarqube` to reach PostgreSQL with the `platform-access=true` label. Set node `vm.max_map_count>=524288`, `fs.file-max>=131072`, and process file/thread limits per SonarSource requirements; privileged sysctl init containers are deliberately disabled. Rotate the initial built-in admin password before exposure.

## Credential contract

| Existing secret | Required keys |
| --- | --- |
| `sonarqube-jdbc` | `password` |
| `sonarqube-monitoring` | `passcode` |

The disposable bootstrap script creates random 48-character values using Python's cryptographic secrets module. It creates new Secrets through stdin with an explicit context, refuses existing names and does not overwrite or rotate production credentials. It does not initialize database schemas or replace an organizational secret manager. Secrets must be created in `sonarqube` before the workload.

Kubernetes Secret base64 encoding is not encryption. Enable API datastore encryption, least-privilege RBAC and secret-manager integration. Rotate credentials using each application's supported procedure, then update the Kubernetes Secret and confirm all clients reconnect.

## Values

`charts/sonarqube/values.yaml` supplies the smaller base profile; `values-production.yaml` overlays production requests/storage. Upstream wrappers nest options under `app`; operator-managed databases expose `clusterSpec`; custom Nexus/Fabric charts expose their fields directly. Review the values files and upstream documentation before adding an option—Helm can silently ignore unknown values.

Set a CSI storage class that meets your failure-domain, expansion and encryption requirements. Never shrink an existing claim by changing a value. Before changing image major versions, validate the supported application and operator upgrade path and restore a backup in isolation.

## Access

`sonarqube.sonarqube.svc.cluster.local:9000`

Services are private ClusterIP endpoints. Label only trusted client namespaces `platform-access=true`, or replace the ingress rule with explicit workload selectors. Add an approved TLS ingress and SSO/authentication where applicable. Egress filtering, external certificates, DNS and monitoring integration remain environment configuration.
