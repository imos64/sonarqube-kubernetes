"""Validate core schemas plus CRDs; refuse unvalidated custom kinds and embedded credentials."""
from pathlib import Path
import subprocess, json, yaml
from jsonschema import Draft7Validator
root = Path(__file__).resolve().parents[1]
streams = list((root / "k8s").glob("*/resources.yaml"))
schema_sources = streams + list((root / "schemas").glob("*.yaml"))
assert len(streams) >= 2, "Missing rendered profiles"
crd_schema = json.loads((root / "schemas/kubernetes-1.34-crd.json").read_text())
schemas = {}
for path in schema_sources:
    for obj in yaml.safe_load_all(path.read_text()):
        if obj and obj.get("kind") == "CustomResourceDefinition":
            for version in obj["spec"]["versions"]:
                schema = version.get("schema", {}).get("openAPIV3Schema")
                if schema:
                    schemas[(obj["spec"]["group"] + "/" + version["name"], obj["spec"]["names"]["kind"])] = schema
core_groups = {"v1", "apps/v1", "batch/v1", "policy/v1", "rbac.authorization.k8s.io/v1", "networking.k8s.io/v1", "autoscaling/v2", "apiextensions.k8s.io/v1", "admissionregistration.k8s.io/v1", "coordination.k8s.io/v1"}
for path in streams:
    core = []; seen = set(); custom_count = 0
    for obj in yaml.safe_load_all(path.read_text()):
        if not obj: continue
        identity = (obj["apiVersion"], obj["kind"], obj["metadata"].get("namespace", ""), obj["metadata"]["name"])
        assert identity not in seen, identity
        seen.add(identity)
        assert obj["kind"] != "Secret" or not any((obj.get("data", {}) | obj.get("stringData", {})).values()), "Never publish generated secret payloads"
        if obj["kind"] == "CustomResourceDefinition":
            Draft7Validator(crd_schema).validate(obj)
        elif obj["apiVersion"] in core_groups:
            core.append(obj)
        else:
            key = (obj["apiVersion"], obj["kind"])
            assert key in schemas, "Missing CRD schema: " + str(key)
            Draft7Validator(schemas[key]).validate(obj)
            custom_count += 1
        if obj["kind"] in ("Deployment", "StatefulSet", "DaemonSet", "Job"):
            for container in obj["spec"]["template"]["spec"].get("containers", []):
                assert not container["image"].endswith(":latest"), container["image"]
    result = subprocess.run(["kubeconform", "-strict", "-summary", "-kubernetes-version", "1.34.0"], input=yaml.safe_dump_all(core), text=True)
    assert result.returncode == 0, path
    print(path.parent.name, "custom resources validated:", custom_count)
print("PASS: core/CRD schemas, unique resources, no embedded credentials, no latest container tags")

# Optional site overlays must remain compatible with the supplied operator schemas.
pkg = json.loads((root / "package.json").read_text())
for example in (root / "examples").glob("*-values.yaml"):
    rendered = subprocess.check_output(["helm", "template", pkg["name"], str(root / "charts" / pkg["name"]), "-n", pkg["namespace"], "-f", str(example)], text=True)
    for obj in yaml.safe_load_all(rendered):
        if obj and (obj["apiVersion"], obj["kind"]) in schemas:
            Draft7Validator(schemas[(obj["apiVersion"], obj["kind"])]).validate(obj)
    print("Optional overlay validated:", example.name)
