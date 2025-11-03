import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
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
    Path("scanners/tfsec_outputs").mkdir(parents=True, exist_ok=True)
    Path("merged_findings_v2").mkdir(parents=True, exist_ok=True)


def run_tfsec_on_dir(tfsec_cmd: str, target_dir: Path, timeout: int = 120):
    # tfsec scans directories. We'll copy the file into a temp dir and scan.
    cmd = [tfsec_cmd, "--format", "json", str(target_dir)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if out.returncode not in (0, 1):  # tfsec returns 1 when issues found
            return None, f"rc={out.returncode} stderr={out.stderr.strip()}"
        if not out.stdout.strip():
            return None, "empty stdout"
        return json.loads(out.stdout), None
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except Exception as e:
        return None, f"exception: {e}"


def normalize_tfsec(json_obj, original_file: Path):
    rows = []
    # tfsec JSON often has 'results' or 'issues'
    issues = []
    if isinstance(json_obj, dict):
        issues = json_obj.get("results") or json_obj.get("issues") or []
    if isinstance(issues, dict):
        issues = issues.get("issues", [])
    for it in issues:
        rows.append({
            "file_path": str(original_file),
            "scanner": "tfsec",
            "check_id": it.get("rule_id") or it.get("ruleID") or it.get("id"),
            "severity": (it.get("severity") or it.get("level") or "").upper(),
            "message": it.get("description") or it.get("message"),
            "resource": it.get("resource") or it.get("resourceName"),
            "guideline": it.get("link") or it.get("documentationURL"),
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Batch scan IaC files with tfsec")
    parser.add_argument("--iac-dir", default="iac_files", help="Root directory of IaC files")
    parser.add_argument("--start", type=int, default=0, help="Start offset of files")
    parser.add_argument("--limit", type=int, default=200, help="Max files to process in this batch")
    parser.add_argument("--batch-index", type=int, default=0, help="Batch index used in output filename")
    parser.add_argument("--tfsec-cmd", default="tfsec", help="Path to tfsec binary")
    parser.add_argument("--timeout", type=int, default=120, help="Per-file timeout seconds")
    args = parser.parse_args()

    ensure_dirs()
    iac_root = Path(args.iac_dir)
    files = list(iter_iac_files(iac_root))
    files.sort()

    sel = files[args.start: args.start + args.limit]
    out_csv = Path("scanners/tfsec_outputs") / f"batch{args.batch_index}.csv"
    log_path = Path("scan_log_tfsec.txt")

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
            # tfsec needs a folder; copy file into a temp dir
            with tempfile.TemporaryDirectory() as td:
                tmp_dir = Path(td)
                try:
                    target = tmp_dir / fp.name
                    target.write_bytes(Path(fp).read_bytes())
                except Exception as e:
                    log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {fp} | ERROR | copy: {e}\n")
                    processed += 1
                    continue

                js, err = run_tfsec_on_dir(args.tfsec_cmd, tmp_dir, timeout=args.timeout)
                if js is None:
                    log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {fp} | ERROR | {err}\n")
                else:
                    rows = normalize_tfsec(js, fp)
                    for r in rows:
                        writer.writerow({k: r.get(k, "") for k in SCHEMA})
                        total_rows += 1
            processed += 1
            if processed % 25 == 0:
                print(f"Processed {processed}/{len(sel)} files...")

    dt = time.time() - t0
    print(f"tfsec batch done. files={processed}, rows={total_rows}, time={dt:.1f}s, out={out_csv}")


if __name__ == "__main__":
    sys.exit(main())
