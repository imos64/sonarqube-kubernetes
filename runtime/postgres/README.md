# PostgreSQL candidate for local SonarQube

This candidate is **not a deployed release**. SonarQube and its database remain
disabled until both exact published images pass the existing HIGH/CRITICAL and
secret gate, followed by reviewed GitOps qualification.

The official PostgreSQL 17.11 Alpine 3.24 image avoids the Debian package
findings in the previously prepared image. Its only retained HIGH/CRITICAL
findings are in Go 1.24.6 embedded in `gosu` 1.19. This Dockerfile rebuilds the
**unchanged** `tianon/gosu` 1.19 source at
`6456aaa0f3c854d199d0f037f068eb97515b7513` using pinned Go 1.27.1.
It preserves PostgreSQL, the entry point and all runtime packages. Nothing is
excluded from vulnerability or secret scanning. The runtime defaults to UID/GID
70, matching the Alpine postgres account; a future Helm profile must use 70 for
runAsUser, runAsGroup and fsGroup.

`sources.lock.json` pins the official runtime and builder images and the SHA-256
of `gosu-source.tar`, generated with `git archive` at that exact upstream commit.
The archive includes upstream source, go.mod, go.sum, license and test scripts.
Go module checksums are verified; CGO is disabled as in upstream's build.
The compiled Go version and module inventory remain available to scanners.

From a clean commit, run:

```sh
python3 scripts/qualify_postgres.py --output evidence/postgres
```

The same command runs in CI. It builds the exact checked-in inputs, scans all
runtime packages with pinned Trivy 0.74.0 and empty ignore/config files, emits a
CycloneDX SBOM, and checks password authentication, restricted startup, restart
persistence and a 10,000-row dump/restore into a separate disposable container
and volume. Fixtures have no network or host ports and touch no cluster.
Evidence, including failed attempts, is retained. No image is published by CI.

This fixture restore is **local-only** and is not Sonar analysis-history restore
acceptance. `durably_accepted=false`; an independent backup target remains
unestablished. The Sonar image's separate Java-library findings are not repaired
by this database change.
