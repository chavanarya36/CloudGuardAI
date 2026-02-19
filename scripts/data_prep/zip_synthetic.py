"""Utilities for zipping synthetic test samples.

This module is now import-safe: importing it does not perform any
filesystem operations or exit the interpreter. Runtime behaviour is
exposed via functions and an optional CLI entry point.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import Iterable


def get_repo_root() -> Path:
    """Return the repository root inferred from this file location."""

    return Path(__file__).resolve().parents[1]


def get_default_paths() -> tuple[Path, Path]:
    """Return (base_dir, output_zip) default paths for synthetic samples."""

    repo_root = get_repo_root()
    base = repo_root / "real_test_samples" / "synthetic"
    out = repo_root / "synthetic_samples.zip"
    return base, out


def list_files(base: Path) -> Iterable[Path]:
    """Yield all files under *base* recursively.

    This helper is separated for testability and reuse.
    """

    if not base.exists():
        return []
    return (p for p in base.rglob("*") if p.is_file())


def create_zip_from_dir(base: Path, out: Path) -> None:
    """Create a ZIP archive at *out* containing files under *base*.

    Raises FileNotFoundError if *base* does not exist. The function does
    not exit the interpreter and can be safely used from tests.
    """

    if not base.exists():
        raise FileNotFoundError(f"Base folder not found: {base}")

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in list_files(base):
            z.write(p, p.relative_to(base))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point used by tests or manual runs.

    Returns 0 on success, non-zero on failure. Errors are printed to
    stderr instead of raising SystemExit at import time.
    """

    import argparse

    parser = argparse.ArgumentParser(description="Zip synthetic test samples.")
    parser.add_argument(
        "--base",
        type=Path,
        default=None,
        help="Base directory containing synthetic samples (default: repo_root/real_test_samples/synthetic)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output ZIP path (default: repo_root/synthetic_samples.zip)",
    )

    args = parser.parse_args(argv)

    base, out = get_default_paths()
    if args.base is not None:
        base = args.base
    if args.out is not None:
        out = args.out

    try:
        create_zip_from_dir(base, out)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - unexpected
        print(f"unexpected error: {exc}", file=sys.stderr)
        return 2

    try:
        size = out.stat().st_size
        print(f"Zipped to {out} ({size} bytes)")
    except OSError:
        print(f"Zipped to {out}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

