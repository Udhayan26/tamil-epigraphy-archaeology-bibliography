#!/usr/bin/env python3
"""Union fresh harvest files with the previously saved ones so the collection only grows.
Usage: merge_harvest.py <prev_dir> <new_dir>   (result written into new_dir)"""
import json, sys
from pathlib import Path

prev, new = Path(sys.argv[1]), Path(sys.argv[2])
for pf in sorted(prev.glob("*.json")):
    nf = new / pf.name
    try:
        old = json.loads(pf.read_text(encoding="utf-8"))
    except Exception:
        continue
    try:
        fresh = json.loads(nf.read_text(encoding="utf-8")) if nf.exists() else []
    except Exception:
        fresh = []
    ids = {r.get("source_id") for r in fresh}
    kept = [r for r in old if r.get("source_id") not in ids]
    out = fresh + kept
    nf.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{pf.name}: previous {len(old)}, this run {len(fresh)}, kept from before {len(kept)}, total {len(out)}")
