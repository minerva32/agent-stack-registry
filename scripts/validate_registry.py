#!/usr/bin/env python3
"""Validate all registry YAML entries against entry.schema.json"""
import json, yaml, sys
from pathlib import Path
from jsonschema import validate, ValidationError

schema_path = Path(__file__).parent.parent / "schemas" / "entry.schema.json"
registry_path = Path(__file__).parent.parent / "registry"

with open(schema_path) as f:
    schema = json.load(f)

errors = []
entries = list(registry_path.rglob("*.yaml"))

if not entries:
    print("No entries found.")
    sys.exit(0)

for entry_path in entries:
    with open(entry_path) as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(f"YAML parse error in {entry_path}: {e}")
            continue
    try:
        validate(instance=data, schema=schema)
        print(f"  ✅ {entry_path.relative_to(registry_path)}")
    except ValidationError as e:
        errors.append(f"  ❌ {entry_path.relative_to(registry_path)}: {e.message}")

if errors:
    print("\nValidation errors:")
    for err in errors:
        print(err)
    sys.exit(1)
else:
    print(f"\n✅ All {len(entries)} entries valid.")
