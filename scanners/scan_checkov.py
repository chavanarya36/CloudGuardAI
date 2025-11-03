import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path


SCHEMA = [
    "file_path",
    "scanner",
    "check_id",
    "severity",
    "message",
    "resource",
    "guideline",
]


def iter_iac_files(root: Path):
    exts = {".tf", ".yaml", ".yml", ".json", ".bicep"}
    for r, _, files in os.walk(root):
        for f in files:
            if Path(f).suffix.lower() in exts:
                yield Path(r) / f


def ensure_dirs():
    Path("scanners/checkov_outputs").mkdir(parents=True, exist_ok=True)
    Path("merged_findings_v2").mkdir(parents=True, exist_ok=True)


def run_checkov_on_file(checkov_cmd: str, file_path: Path, timeout: int = 60):
    cmd = [checkov_cmd, "-f", str(file_path), "-o", "json"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        # Checkov returns 1 when violations found, 0 when clean
        if out.returncode not in (0, 1):
            return None, f"rc={out.returncode} stderr={out.stderr.strip()}"
        if not out.stdout.strip():
            return None, "empty stdout"
        return json.loads(out.stdout), None
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except Exception as e:
        return None, f"exception: {e}"


def normalize_checkov(json_obj, file_path: Path):
    rows = []
    try:
        res = json_obj.get("results", {})
        failed = res.get("failed_checks", [])
        for it in failed:
            rows.append({
                "file_path": str(file_path),
                "scanner": "checkov",
                "check_id": it.get("check_id"),
                "severity": (it.get("severity") or "").upper(),
                "message": it.get("check_name"),
                "resource": it.get("resource"),
                "guideline": it.get("guideline"),
            })
    except Exception:
        pass
    return rows


def main():
    parser = argparse.ArgumentParser(description="Batch scan IaC files with Checkov")
    parser.add_argument("--iac-dir", default="iac_files", help="Root directory of IaC files")
    parser.add_argument("--start", type=int, default=0, help="Start offset of files")
    parser.add_argument("--limit", type=int, default=200, help="Max files to process in this batch")
    parser.add_argument("--batch-index", type=int, default=0, help="Batch index used in output filename")
    parser.add_argument("--checkov-cmd", default="checkov", help="Path to checkov binary (or .cmd on Windows)")
    parser.add_argument("--timeout", type=int, default=60, help="Per-file timeout seconds")
    args = parser.parse_args()

    ensure_dirs()
    iac_root = Path(args.iac_dir)
    files = list(iter_iac_files(iac_root))
    files.sort()

    sel = files[args.start: args.start + args.limit]
    out_csv = Path("scanners/checkov_outputs") / f"batch{args.batch_index}.csv"
    log_path = Path(f"scan_log_checkov.txt")

    # Resume-safe: skip if output already exists
    if out_csv.exists():
        print(f"Output exists, skipping: {out_csv}")
        return

    t0 = time.time()
    processed = 0
    total_rows = 0
    with open(out_csv, "w", newline="", encoding="utf-8") as fh, open(log_path, "a", encoding="utf-8") as log:
        writer = csv.DictWriter(fh, fieldnames=SCHEMA)
        writer.writeheader()
        for fp in sel:
            js, err = run_checkov_on_file(args.checkov_cmd, fp, timeout=args.timeout)
            if js is None:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {fp} | ERROR | {err}\n")
            else:
                rows = normalize_checkov(js, fp)
                for r in rows:
                    writer.writerow({k: r.get(k, "") for k in SCHEMA})
                    total_rows += 1
            processed += 1
            if processed % 25 == 0:
                print(f"Processed {processed}/{len(sel)} files...")

    dt = time.time() - t0
    print(f"Checkov batch done. files={processed}, rows={total_rows}, time={dt:.1f}s, out={out_csv}")


if __name__ == "__main__":
    sys.exit(main())
