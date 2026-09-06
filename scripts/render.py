#!/usr/bin/env python3
"""Render pinned chart sources, separating operator bootstrap from workloads."""
from pathlib import Path
import json, subprocess, yaml
root = Path(__file__).resolve().parents[1]
pkg = json.loads((root / "package.json").read_text())
name = pkg["name"]
charts = [root / "charts" / name] + ([root / "operator"] if pkg["operator"] else [])
for chart in charts:
    meta = yaml.safe_load((chart / "Chart.yaml").read_text())
    for index, dep in enumerate(meta.get("dependencies", [])):
        subprocess.run(["helm", "repo", "add", name + "-dependency-" + str(index), dep["repository"]], check=True, stdout=subprocess.DEVNULL)
    if meta.get("dependencies"):
        subprocess.run(["helm", "dependency", "build", str(chart)], check=True)
for profile in ["base", "production"] + (["operator"] if pkg["operator"] else []):
    chart = root / "operator" if profile == "operator" else root / "charts" / name
    command = ["helm", "template", name + "-operator" if profile == "operator" else name, str(chart), "--namespace", pkg["namespace"], "--include-crds", "--skip-tests"]
    if profile == "production":
        command += ["-f", str(chart / "values-production.yaml")]
    text = subprocess.check_output(command, text=True)
    directory = root / "k8s" / profile
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "resources.yaml").write_text("\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n")
    (directory / "kustomization.yaml").write_text(yaml.safe_dump({"apiVersion": "kustomize.config.k8s.io/v1beta1", "kind": "Kustomization", "namespace": pkg["namespace"], "resources": ["resources.yaml"]}, sort_keys=False))
