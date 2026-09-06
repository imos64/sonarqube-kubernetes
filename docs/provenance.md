# Source provenance

Maintainer: [imos64](https://github.com/imos64). Integration package version: 1.0.0. Sources reviewed 2026-09-06.

[Upstream project](https://github.com/SonarSource/helm-chart-sonarqube) · [Official documentation](https://docs.sonarsource.com/sonarqube-community-build/setup-and-upgrade/deploy-on-kubernetes/)

Upstream Helm chart `sonarqube` is pinned to `2026.4.1` from `https://SonarSource.github.io/helm-chart-sonarqube`. Chart dependencies are vendored and locked; `helm dependency build` reproduces the recorded version.

Kubernetes CRD validation schema is the transitive definition subset of the official [Kubernetes v1.34.0 OpenAPI specification](https://github.com/kubernetes/kubernetes/blob/v1.34.0/api/openapi-spec/swagger.json), Apache-2.0. Upstream chart archives include their source templates and original license files where supplied. Container image licensing remains upstream; this deployment license does not relicense those applications.

Image versions are explicit in values or locked upstream charts. Tags are version-pinned, not guaranteed immutable; mirror and pin approved image digests for your production supply chain. Review chart, image, plugin and operator updates as one compatible change.

| Chart archive | SHA-256 |
| --- | --- |
| `charts/sonarqube/charts/sonarqube-2026.4.1.tgz` | `336c4223bd957c14fa8f2abebd614025d7dbb71e8ec458fc749f047a83176ca7` |
