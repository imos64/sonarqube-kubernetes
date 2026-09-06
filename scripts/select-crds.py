import sys,yaml
print(yaml.safe_dump_all(o for o in yaml.safe_load_all(sys.stdin) if o and o.get("kind")=="CustomResourceDefinition"))
