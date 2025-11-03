import os, sys, zipfile
from pathlib import Path

# Resolve repo root relative to this script
repo_root = Path(__file__).resolve().parents[1]
base = repo_root / 'real_test_samples' / 'synthetic'
out = repo_root / 'synthetic_samples.zip'

if not base.exists():
    print(f"Base folder not found: {base}")
    sys.exit(1)

# Create zip
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in base.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(base))

print(f"Zipped to {out}")
try:
    print(f"ZIP size: {out.stat().st_size} bytes")
except Exception:
    pass
