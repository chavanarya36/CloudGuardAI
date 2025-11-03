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
    Path("scanners/kics_outputs").mkdir(parents=True, exist_ok=True)
    Path("merged_findings_v2").mkdir(parents=True, exist_ok=True)


def run_kics_on_dir(kics_cmd: str, target_dir: Path, timeout: int = 180):
    # KICS requires a path; use JSON or SARIF output
    cmd = [
        kics_cmd,
        "scan",
        "-p",
        str(target_dir),
        "--report-formats",
        "json",
        "--no-progress",
        "--quiet",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if out.returncode not in (0, 50, 51):  # KICS returns 50/51 when vulns found
            return None, f"rc={out.returncode} stderr={out.stderr.strip()}"
        # KICS prints path to report or report content depends on version.
        # Try to parse stdout as JSON; if fails, attempt to find report.json in temp dir.
        try:
            return json.loads(out.stdout), None
        except Exception:
            # fallback: search for *.json in target_dir
            for p in target_dir.rglob("*.json"):
                try:
                    return json.loads(p.read_text(encoding="utf-8")), None
                except Exception:
                    continue
            return None, "no json report detected"
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except Exception as e:
        return None, f"exception: {e}"


def normalize_kics(json_obj, original_file: Path):
    rows = []
    # KICS JSON schema: { "queries": [ {"id","severity","query_name","description","platform"...}], "results": [{"query_id","message","file_name","line"...}] }
    try:
        queries = {q.get("id"): q for q in json_obj.get("queries", [])}
        for res in json_obj.get("results", []):
            qid = res.get("query_id") or res.get("id")
            q = queries.get(qid, {})
            rows.append({
                "file_path": str(original_file),
                "scanner": "kics",
                "check_id": qid,
                "severity": (q.get("severity") or res.get("severity") or "").upper(),
                "message": res.get("message") or q.get("query_name") or q.get("description"),
                "resource": res.get("resource_name") or res.get("file_name"),
                "guideline": q.get("description") or q.get("url") or "",
            })
    except Exception:
        pass
    return rows


def main():
    parser = argparse.ArgumentParser(description="Batch scan IaC files with KICS")
    parser.add_argument("--iac-dir", default="iac_files", help="Root directory of IaC files")
    parser.add_argument("--start", type=int, default=0, help="Start offset of files")
    parser.add_argument("--limit", type=int, default=200, help="Max files to process in this batch")
    parser.add_argument("--batch-index", type=int, default=0, help="Batch index used in output filename")
    parser.add_argument("--kics-cmd", default="kics", help="Path to kics binary")
    parser.add_argument("--timeout", type=int, default=180, help="Per-file timeout seconds")
    args = parser.parse_args()

    ensure_dirs()
    iac_root = Path(args.iac_dir)
    files = list(iter_iac_files(iac_root))
    files.sort()

    sel = files[args.start: args.start + args.limit]
    out_csv = Path("scanners/kics_outputs") / f"batch{args.batch_index}.csv"
    log_path = Path("scan_log_kics.txt")

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
            # KICS scans directories; place single file into a temp dir
            with tempfile.TemporaryDirectory() as td:
                tmp_dir = Path(td)
                try:
                    target = tmp_dir / fp.name
                    target.write_bytes(Path(fp).read_bytes())
                except Exception as e:
                    log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {fp} | ERROR | copy: {e}\n")
                    processed += 1
                    continue

                js, err = run_kics_on_dir(args.kics_cmd, tmp_dir, timeout=args.timeout)
                if js is None:
                    log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {fp} | ERROR | {err}\n")
                else:
                    rows = normalize_kics(js, fp)
                    for r in rows:
                        writer.writerow({k: r.get(k, "") for k in SCHEMA})
                        total_rows += 1
            processed += 1
            if processed % 25 == 0:
                print(f"Processed {processed}/{len(sel)} files...")

    dt = time.time() - t0
    print(f"KICS batch done. files={processed}, rows={total_rows}, time={dt:.1f}s, out={out_csv}")


if __name__ == "__main__":
    sys.exit(main())
