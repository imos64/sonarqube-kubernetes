#!/usr/bin/env python3
"""Create fresh disposable evaluation secrets; never overwrite existing credentials."""
import argparse, json, secrets, subprocess
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--context", required=True)
a = p.parse_args()
namespace = 'sonarqube'
contracts = {'sonarqube-jdbc': {'password': 'RANDOM'}, 'sonarqube-monitoring': {'passcode': 'RANDOM'}}
k = ["kubectl", "--context", a.context, "-n", namespace]
subprocess.run(k + ["get", "namespace", namespace], check=True, stdout=subprocess.DEVNULL)
for name in contracts:
    probe = subprocess.run(k + ["get", "secret", name, "--ignore-not-found", "-o", "name"], check=True, capture_output=True, text=True)
    if probe.stdout.strip():
        raise SystemExit("Refusing to overwrite existing secret: " + name)
for name, keys in contracts.items():
    obj = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": name, "namespace": namespace}, "type": "Opaque", "stringData": {k: secrets.token_hex(24) if v == "RANDOM" else v for k,v in keys.items()}}
    subprocess.run(k + ["create", "-f", "-"], input=json.dumps(obj), text=True, check=True, stdout=subprocess.DEVNULL)
    print("Created", name, "(values withheld)")
if not contracts:
    print("No static bootstrap secret required. Follow the application/operator bootstrap procedure in docs/configuration.md.")
