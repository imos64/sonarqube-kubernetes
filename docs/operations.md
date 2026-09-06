# Operations and recovery

## Daily health

Wait for the application rollout and `/api/system/status` to report UP. Authenticate, scan a small test project, verify its quality gate, restart the pod, and confirm project history persists. A healthy PostgreSQL pod alone is insufficient.

Observe ready members, replication lag, quorum/elections, disk capacity, CPU throttling, memory pressure, certificate expiry and backup age. Route actionable alerts to an on-call owner. Integrate metrics with [Prometheus](https://github.com/imos64/prometheus-kubernetes/tree/main), dashboards with [Grafana](https://github.com/imos64/grafana-kubernetes/tree/main), logs with [Loki](https://github.com/imos64/loki-kubernetes/tree/main), and notifications with [Alertmanager](https://github.com/imos64/alertmanager-kubernetes/tree/main). Those integrations are not silently installed by this package.

## Backup

PostgreSQL is the authoritative application state. Schedule database backups and retain extension/plugin versions and configuration. Restore PostgreSQL first, start the matching SonarQube version in isolation, let search indexes rebuild, and validate project history, users and quality gates. Coordinate DB migration rollback with a pre-upgrade backup.

```bash
kubectl get pods,pvc -n sonarqube
# Use the PostgreSQL backup procedure for database sonarqube.
# Restore to an isolated database and override app.jdbcOverwrite.jdbcUrl before starting SonarQube.
```

Choose and document RPO, RTO, encryption keys, retention, immutable/off-site storage and an owner. Backup schedules and object-store credentials must be configured before production traffic. Monitor the age of the last successful backup and restore drill; do not equate a completed upload with a recoverable database.

## Restore drill

1. Allocate an isolated namespace/cluster, new credentials and fresh volumes. Block production clients and outgoing notifications.
2. Restore the documented application/database version, configuration, data and required encryption keys from one consistent recovery point.
3. Run application-level integrity checks and compare a known pre-backup marker. Measure elapsed recovery time and the latest recovered transaction.
4. Exercise the normal client path, authentication, authorization and failure handling. Record evidence without credentials.
5. Approve cutover only after the recovered data and client behavior meet the agreed RPO/RTO. Keep the original volumes until recovery is accepted.

## Failure handling

Community supports one application instance. Do not increase replicas or share the embedded search data directory. Multi-node SonarQube requires the supported Data Center edition and a separate licensed architecture.

Check pod events, PVC binding/attachment, node placement, operator logs and cluster membership first. A Pending pod with required anti-affinity may mean insufficient workers; weakening placement hides the failure-domain problem. Never remove multiple quorum members, force a new primary or delete claims to make a dashboard green.

## Upgrade and rollback

Capture an application-consistent backup and prove restore first. Review pinned chart/image/CRD changes, regenerate manifests, run validation, and test in a separate cluster. Upgrade operators/CRDs according to upstream compatibility rules before their custom resources. Change one database member at a time. Helm rollback cannot reverse database schema or on-disk format migrations; use the application's documented downgrade/restore path.

## Decommission

Export and verify a final backup. Stop clients and confirm no workload depends on the service. Remove the release using its single delivery owner. Inspect retained PVCs and operator CR deletion/finalizer behavior before deleting anything else. Do not delete shared CRDs or namespaces as a routine rollback.
