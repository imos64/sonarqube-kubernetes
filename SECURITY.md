# Security

Report suspected credential exposure or vulnerabilities through this repository's private security reporting page. Do not open public issues with credentials, private keys, kubeconfigs, customer data or Terraform state.

Existing-secret references keep credential payloads out of Git. Supply credentials with a secret manager, enforce Kubernetes RBAC and datastore encryption, restrict administrative access and use approved TLS certificates. The included NetworkPolicies require an enforcing CNI; ingress permits the workload namespace and namespaces labeled `platform-access=true`, and egress remains unrestricted. Review these trust boundaries for your site.

Do not expose database, browser automation, CI, repository or GitOps admin interfaces directly to the internet. Apply least-privilege application users, SSO and authenticated ingress as appropriate. Operators may require cluster-wide RBAC and admission webhooks; review upstream permissions before installation.

Validation is not a security certification. Scan pinned application images/plugins and review upstream advisories before deployment. Rotate compromised credentials through the application's supported procedure and verify both server and client recovery.
