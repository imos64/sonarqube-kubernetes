# Local Argo qualification

This repository supplies the Helm chart to an explicitly pinned Argo Application. The local deployment values and exact multi-source references are reviewed in `teckixora/platform-infrastructure` PR #2. One Argo owner manages each release; do not install a second Helm/Terraform release.

`workloadNetworkPolicy.enabled=false` is permitted only with the separately rendered default-deny and service-specific policies in the infrastructure release. The shared `platform-access=true` namespace allowance is not used for the local deployment. Services remain ClusterIP, no Ingress is created, and authenticated NGINX endpoints are accessed by loopback-only port forwards. No public tunnel, Cloudflare or DNS configuration changes are made.

The local profile retains nonroot execution, read-only root filesystems, dropped capabilities, RuntimeDefault seccomp, no service-account token, immutable images and bounded resources. Grid uses one Chromium worker with one session; no Firefox/Edge/video/autoscaler. Sonar uses one Community instance and a dedicated PostgreSQL/PVC; analysis is serialized. Credentials are supplied separately and never committed.

Rendering uses only checksum-locked vendored dependencies. `scripts/render.py` never refreshes a mutable upstream chart during validation. Kubernetes 1.36.1 and Argo Helm 4.2.1 are the actual local target; rendering/admission and runtime results are separate evidence. No upstream Kubernetes support promise is inferred from local success. The infrastructure release must record real startup, authentication, analysis/browser sessions, persistence and capacity before acceptance.
