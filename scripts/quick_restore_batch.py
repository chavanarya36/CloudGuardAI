#!/usr/bin/env python3
"""
Quick batch restoration - restore first N repositories to estimate dataset size
"""

import os
import sys
import csv
import subprocess
import shutil
from pathlib import Path
import time
import re

csv.field_size_limit(10 * 1024 * 1024)

IAC_EXTENSIONS = {'.tf', '.yaml', '.yml', '.json', '.bicep', '.hcl'}

def get_needed_repos(labels_csv: str, limit: int = None):
    """Extract unique repo IDs from labels"""
    repos = []
    seen = set()
    
    with open(labels_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            match = re.search(r'iac_subset[/\\]([^/\\]+)', row.get('abs_path', ''))
            if match:
                repo_id = match.group(1)
                if repo_id not in seen:
                    repos.append(repo_id)
                    seen.add(repo_id)
                    if limit and len(repos) >= limit:
                        break
    
    return repos

def get_clone_url(repo_id: str, repos_csv: str = "repositories.csv"):
    """Get clone URL for a repo ID"""
    with open(repos_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('ID', '').strip() == repo_id:
                api_url = row.get('url', '').strip()
                name = row.get('name', '').strip()
                
                if 'api.github.com/repos/' in api_url:
                    return api_url.replace('api.github.com/repos/', 'github.com/')
                elif name and '/' in name:
                    return f"https://github.com/{name}"
    
    return None

def clone_and_extract(repo_id: str, clone_url: str, output_dir: Path):
    """Clone repo and extract IaC files"""
    temp = Path("temp_clones") / repo_id
    
    # Check if already done
    if (output_dir / repo_id).exists():
        files = list((output_dir / repo_id).rglob('*'))
        return len([f for f in files if f.is_file() and f.suffix.lower() in IAC_EXTENSIONS])
    
    # Clean temp
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    
    # Clone
    try:
        cmd = ['git', 'clone', '--depth=1', '--quiet', clone_url, str(temp)]
        result = subprocess.run(cmd, timeout=180, capture_output=True)
        if result.returncode != 0:
            return 0
    except:
        return 0
    
    # Find and copy IaC files
    repo_out = output_dir / repo_id
    repo_out.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    for root, dirs, files in os.walk(temp):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '.venv', '__pycache__'}]
        
        for file in files:
            if Path(file).suffix.lower() in IAC_EXTENSIONS:
                src = Path(root) / file
                try:
                    # Preserve structure
                    rel = src.relative_to(temp)
                    dest = repo_out / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    copied += 1
                except:
                    pass
    
    # Cleanup
    shutil.rmtree(temp, ignore_errors=True)
    
    return copied

def main():
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    
    print(f"\n{'='*70}")
    print(f"🚀 Quick Batch Restoration — First {batch_size} Repositories")
    print(f"{'='*70}\n")
    
    output_dir = Path("iac_full")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get repos to process
    print("📋 Extracting repository IDs from labels...")
    repos = get_needed_repos("iac_labels_clean.csv", limit=batch_size)
    print(f"✅ Will process {len(repos)} repositories\n")
    
    # Process each
    total_files = 0
    successful = 0
    start = time.time()
    
    for idx, repo_id in enumerate(repos, 1):
        print(f"[{idx}/{len(repos)}] {repo_id}...", end=' ', flush=True)
        
        clone_url = get_clone_url(repo_id)
        if not clone_url:
            print("❌ URL not found")
            continue
        
        files = clone_and_extract(repo_id, clone_url, output_dir)
        
        if files > 0:
            print(f"✅ {files} files")
            total_files += files
            successful += 1
        else:
            print("⚠️  No IaC files")
    
    elapsed = time.time() - start
    
    # Summary
    print(f"\n{'='*70}")
    print("✅ Batch Complete")
    print(f"{'='*70}\n")
    print(f"📊 Results:")
    print(f"  Repositories processed: {len(repos)}")
    print(f"  Successful: {successful}")
    print(f"  Total IaC files: {total_files}")
    print(f"  Average: {total_files/max(successful,1):.1f} files/repo")
    print(f"  Time: {elapsed:.1f}s ({elapsed/len(repos):.1f}s per repo)\n")
    
    # Estimate full restore
    if successful > 0:
        avg_per_repo = total_files / successful
        est_total = int(103 * avg_per_repo)
        est_time = int((103 / len(repos)) * elapsed)
        
        print(f"📈 Full Restoration Estimate (103 repos):")
        print(f"  Expected files: ~{est_total:,}")
        print(f"  Estimated time: ~{est_time//60}min {est_time%60}s\n")

if __name__ == '__main__':
    main()
