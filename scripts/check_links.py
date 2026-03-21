#!/usr/bin/env python3
"""Check all homepage links in registry entries."""
import yaml, requests, sys
from pathlib import Path

registry_path = Path(__file__).parent.parent / "registry"
dead = []

for entry_path in registry_path.rglob("*.yaml"):
    with open(entry_path) as f:
        data = yaml.safe_load(f)
    url = data.get("homepage")
    if not url:
        continue
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        if r.status_code >= 400:
            dead.append(f"  ❌ {entry_path.name}: {url} → {r.status_code}")
        else:
            print(f"  ✅ {entry_path.name}: {url}")
    except Exception as e:
        dead.append(f"  ⚠️  {entry_path.name}: {url} → {e}")

if dead:
    print("\nDead links:")
    for d in dead:
        print(d)
    sys.exit(1)
else:
    print("\n✅ All links alive.")
