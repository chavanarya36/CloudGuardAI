"""Root pytest configuration — ensures all subproject paths are on sys.path."""
import sys
from pathlib import Path

root = Path(__file__).parent
for sub in ["api", "ml", "rules"]:
    p = str(root / sub)
    if p not in sys.path:
        sys.path.insert(0, p)
