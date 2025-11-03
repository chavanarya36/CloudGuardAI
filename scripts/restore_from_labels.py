#!/usr/bin/env python3
"""
Smart IaC Dataset Restoration
Only clones repositories that were in the original labeled dataset.
Extracts repository IDs from iac_labels_clean.csv and clones them.
"""

import os
import sys
import csv
import subprocess
import shutil
from pathlib import Path
from typing import Set, Dict
import time
import re

# Increase CSV field size limit
csv.field_size_limit(10 * 1024 * 1024)  # 10 MB

# IaC file extensions
IAC_EXTENSIONS = {'.tf', '.yaml', '.yml', '.json', '.bicep', '.hcl'}

def extract_repo_ids_from_labels(labels_csv: str = "iac_labels_clean.csv") -> Set[str]:
    """
    Extract unique repository IDs from labeled dataset.
    """
    repo_ids = set()
    
    print(f"📋 Reading labeled dataset: {labels_csv}")
    
    with open(labels_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            abs_path = row.get('abs_path', '')
            
            # Extract repo ID from path like: iac_subset/REPO_ID/...
            match = re.search(r'iac_subset[/\\]([^/\\]+)', abs_path)
            if match:
                repo_ids.add(match.group(1))
    
    print(f"✅ Found {len(repo_ids)} unique repositories\n")
    return repo_ids

def load_repository_map(repos_csv: str = "repositories.csv") -> Dict[str, str]:
    """
    Load mapping of repo_id -> clone_url from repositories.csv.
    """
    repo_map = {}
    
    print(f"📋 Loading repository URLs: {repos_csv}")
    
    with open(repos_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            repo_id = row.get('ID', '').strip()
            api_url = row.get('url', '').strip()
            name = row.get('name', '').strip()
            
            if not repo_id:
                continue
            
            # Convert API URL to clone URL
            if 'api.github.com/repos/' in api_url:
                clone_url = api_url.replace('api.github.com/repos/', 'github.com/')
            elif name and '/' in name:
                clone_url = f"https://github.com/{name}"
            else:
                continue
            
            repo_map[repo_id] = clone_url
    
    print(f"✅ Loaded {len(repo_map)} repository URLs\n")
    return repo_map

def clone_repo(repo_url: str, dest_path: Path, timeout: int = 180) -> bool:
    """
    Clone a repository with timeout protection.
    """
    try:
        cmd = ['git', 'clone', '--depth=1', '--quiet', repo_url, str(dest_path)]
        result = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def find_iac_files(repo_path: Path) -> list:
    """
    Find all IaC files in repository.
    """
    iac_files = []
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {
            '.git', 'node_modules', '.venv', 'venv', '__pycache__'
        }]
        
        for file in files:
            if Path(file).suffix.lower() in IAC_EXTENSIONS:
                iac_files.append(Path(root) / file)
    
    return iac_files

def copy_iac_files(iac_files: list, repo_id: str, output_dir: Path) -> int:
    """
    Copy IaC files preserving directory structure.
    """
    repo_output = output_dir / repo_id
    repo_output.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    for src_file in iac_files:
        try:
            # Get relative path from repo root
            rel_parts = src_file.parts[src_file.parts.index('temp_clones')+2:]
            rel_path = Path(*rel_parts)
            
            dest_file = repo_output / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_file, dest_file)
            copied += 1
        except Exception as e:
            pass
    
    return copied

def main():
    print("\n" + "=" * 70)
    print("🎯 CloudGuard AI — Smart Dataset Restoration")
    print("=" * 70 + "\n")
    
    # Setup
    output_dir = Path("iac_full")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dir = Path("temp_clones")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Extract repo IDs from labels
    needed_repos = extract_repo_ids_from_labels()
    
    if not needed_repos:
        print("❌ No repository IDs found in labeled dataset")
        return
    
    # Step 2: Load repository URLs
    repo_map = load_repository_map()
    
    # Find matching repos
    matched_repos = {}
    for repo_id in needed_repos:
        if repo_id in repo_map:
            matched_repos[repo_id] = repo_map[repo_id]
    
    print(f"📊 Match Results:")
    print(f"  Needed repos: {len(needed_repos)}")
    print(f"  Found in repositories.csv: {len(matched_repos)}")
    print(f"  Missing: {len(needed_repos) - len(matched_repos)}\n")
    
    if not matched_repos:
        print("❌ No matching repositories found")
        return
    
    # Step 3: Clone and extract
    print(f"🚀 Starting restoration of {len(matched_repos)} repositories\n")
    
    stats = {
        'attempted': 0,
        'cloned': 0,
        'with_iac': 0,
        'total_files': 0,
        'failed': []
    }
    
    start_time = time.time()
    
    for idx, (repo_id, clone_url) in enumerate(matched_repos.items(), 1):
        print(f"[{idx}/{len(matched_repos)}] {repo_id}")
        
        stats['attempted'] += 1
        
        # Skip if already exists
        if (output_dir / repo_id).exists():
            print(f"  ✅ Already exists")
            existing = list((output_dir / repo_id).rglob('*'))
            stats['total_files'] += len([f for f in existing if f.is_file()])
            stats['with_iac'] += 1
            continue
        
        # Clone
        clone_path = temp_dir / repo_id
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)
        
        print(f"  📥 Cloning...", end=' ', flush=True)
        if not clone_repo(clone_url, clone_path, timeout=180):
            print("❌")
            stats['failed'].append(repo_id)
            continue
        
        print("✅")
        stats['cloned'] += 1
        
        # Find IaC files
        print(f"  🔍 Finding IaC files...", end=' ', flush=True)
        iac_files = find_iac_files(clone_path)
        print(f"{len(iac_files)} found")
        
        if iac_files:
            # Copy
            print(f"  📋 Copying...", end=' ', flush=True)
            copied = copy_iac_files(iac_files, repo_id, output_dir)
            print(f"✅ {copied} files")
            
            stats['with_iac'] += 1
            stats['total_files'] += copied
        
        # Cleanup
        shutil.rmtree(clone_path, ignore_errors=True)
        
        # Progress update
        if idx % 50 == 0:
            elapsed = time.time() - start_time
            avg = elapsed / idx
            remaining = (len(matched_repos) - idx) * avg
            print(f"\n  ⏱️  Progress: {idx}/{len(matched_repos)} | " +
                  f"Files: {stats['total_files']} | " +
                  f"ETA: {remaining/60:.1f}min\n")
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Summary
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("✅ RESTORATION COMPLETE")
    print("=" * 70)
    print(f"\n📊 Final Statistics:")
    print(f"  Repositories attempted: {stats['attempted']}")
    print(f"  Successfully cloned: {stats['cloned']}")
    print(f"  With IaC files: {stats['with_iac']}")
    print(f"  Total IaC files: {stats['total_files']}")
    print(f"  Failed: {len(stats['failed'])}")
    print(f"\n⏱️  Total time: {elapsed/60:.1f} minutes")
    print(f"📁 Output: {output_dir.absolute()}\n")
    
    # Count by extension
    print("📋 File Breakdown:")
    ext_counts = {}
    for ext in IAC_EXTENSIONS:
        count = len(list(output_dir.rglob(f'*{ext}')))
        if count > 0:
            ext_counts[ext] = count
            print(f"  {ext:8s} : {count:,}")
    
    print(f"  {'─'*8}   {'─'*10}")
    print(f"  {'Total':8s} : {sum(ext_counts.values()):,}\n")

if __name__ == '__main__':
    main()
