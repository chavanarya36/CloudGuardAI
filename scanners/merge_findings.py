import argparse
import csv
from pathlib import Path
import pandas as pd

SCHEMA = [
    "file_path",
    "scanner",
    "check_id",
    "severity",
    "message",
    "resource",
    "guideline",
]


def collect_batches():
    roots = [
        ("checkov", Path("scanners/checkov_outputs")),
        ("tfsec", Path("scanners/tfsec_outputs")),
        ("kics", Path("scanners/kics_outputs")),
    ]
    rows = []
    for scanner, root in roots:
        if not root.exists():
            continue
        for p in sorted(root.glob("batch*.csv")):
            try:
                df = pd.read_csv(p)
                # ensure schema and scanner column
                for col in SCHEMA:
                    if col not in df.columns:
                        df[col] = ""
                df = df[SCHEMA]
                # If scanner is blank in file, fill with scanner name
                df["scanner"] = df["scanner"].replace({"": scanner}).fillna(scanner)
                rows.append(df)
            except Exception:
                continue
    if rows:
        return pd.concat(rows, ignore_index=True)
    return pd.DataFrame(columns=SCHEMA)


def main():
    parser = argparse.ArgumentParser(description="Merge scanner batch outputs into a single CSV")
    parser.add_argument("--output", default="merged_findings_v2/merged_findings_v2.csv", help="Path to merged CSV")
    parser.add_argument("--sample", type=int, default=600, help="Number of rows to also write as sample")
    parser.add_argument("--sample-output", default="merged_findings_v2_sample.csv", help="Sample CSV filename in project root")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = collect_batches()
    df.to_csv(out_path, index=False)

    # also write small sample at project root for quick inspection
    sample = df.head(args.sample)
    sample.to_csv(Path(args.sample_output), index=False)

    print(f"Merged {len(df)} findings")
    print(f"Output saved to {out_path}")
    print(f"Sample saved to {args.sample_output}")


if __name__ == "__main__":
    main()
