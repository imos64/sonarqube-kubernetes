# Contributing

Keep chart values, native manifests, architecture and operations documentation consistent. Do not commit secret payloads, certificates/private keys, kubeconfigs, state files, plans or real customer configuration.

Pin dependency versions, preserve upstream attribution and review compatibility across charts, operators and images. Run `make render` and `make validate` before opening a change. Include the relevant application-level acceptance evidence for behavior changes; distinguish schema validation, runtime smoke tests, failover tests and restore drills.

Do not increase replicas for a single-writer application to imply unsupported HA. Explain storage, quorum, fault-domain and edition/licensing assumptions in the README.
