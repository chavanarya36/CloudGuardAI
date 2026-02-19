"""
Prepare a sample batch of IaC files for scanner testing.
Copies first N files from master_iac_list.csv to iac_files/ directory.
"""
import pandas as pd
import shutil
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Prepare sample IaC files for scanning")
    parser.add_argument("--inventory", default="labels_artifacts/iac_labels_clean.csv", help="Path to inventory CSV")
    parser.add_argument("--output-dir", default="iac_files", help="Output directory for files")
    parser.add_argument("--limit", type=int, default=200, help="Number of files to copy")
    args = parser.parse_args()
    
    df = pd.read_csv(args.inventory)
    print(f"Loaded inventory: {len(df)} files")
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    skipped = 0
    errors = 0
    target = args.limit
    
    for idx, row in df.iterrows():
        if copied >= target:
            break
        src = Path(row['abs_path'])
        if not src.exists():
            skipped += 1
            continue
        
        # Preserve relative structure from iac_subset
        try:
            rel = src.relative_to(Path('iac_subset'))
            dest = out_dir / rel
        except ValueError:
            # Not under iac_subset, use basename
            dest = out_dir / src.name
        
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(src, dest)
            copied += 1
            if copied % 50 == 0:
                print(f"Copied {copied} files...")
        except Exception as e:
            errors += 1
    
    print(f"\n✅ Sample preparation complete")
    print(f"   Copied: {copied}")
    print(f"   Skipped (not found): {skipped}")
    print(f"   Errors: {errors}")
    print(f"   Output: {out_dir}")

if __name__ == "__main__":
    main()
