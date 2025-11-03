#!/usr/bin/env python3
"""
Restore IaC Dataset from Repository List
Clones GitHub repositories and extracts IaC files to iac_full/ directory.
Optimized for minimal token usage and production safety.
"""

import os
import sys
import csv
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple
import time
import argparse

# IaC file extensions to search for
IAC_EXTENSIONS = {'.tf', '.yaml', '.yml', '.json', '.bicep', '.hcl'}

def parse_args():
    parser = argparse.ArgumentParser(description='Restore IaC dataset from repository CSV')
    parser.add_argument('--repo-csv', default='repositories.csv', help='CSV with repository info')
    parser.add_argument('--output-dir', default='iac_full', help='Output directory for IaC files')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of repos to clone')
    parser.add_argument('--start', type=int, default=0, help='Start index in CSV')
    parser.add_argument('--clone-timeout', type=int, default=180, help='Timeout per clone (seconds)')
    return parser.parse_args()

def get_repo_list(csv_path: str, start: int = 0, limit: int = None) -> List[Tuple[str, str]]:
    """
    Read repository list from repositories.csv.
    Returns: [(repo_id, github_clone_url), ...]
    
    Expected CSV columns: ID, url, name
    Where 'url' is API URL like https://api.github.com/repos/owner/repo
    """
    repos = []
    
    if not os.path.exists(csv_path):
        print(f"❌ Repository CSV not found: {csv_path}")
        return repos
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            if idx < start:
                continue
            if limit and len(repos) >= limit:
                break
            
            repo_id = row.get('ID', '').strip()
            api_url = row.get('url', '').strip()
            name = row.get('name', '').strip()
            
            # Skip invalid entries
            if not repo_id or not api_url:
                continue
            
            # Convert API URL to clone URL
            # https://api.github.com/repos/owner/repo -> https://github.com/owner/repo
            if 'api.github.com/repos/' in api_url:
                clone_url = api_url.replace('api.github.com/repos/', 'github.com/')
            elif name and '/' in name:
                # Use name field if available (format: owner/repo)
                clone_url = f"https://github.com/{name}"
            else:
                continue
            
            repos.append((repo_id, clone_url))
    
    return repos

def clone_repo(repo_url: str, dest_path: Path, timeout: int = 300) -> bool:
    """
    Clone a single repository with timeout protection.
    Returns True on success, False on failure.
    """
    try:
        # Use --depth=1 for shallow clone (faster, less disk space)
        cmd = ['git', 'clone', '--depth=1', '--quiet', repo_url, str(dest_path)]
        
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        print(f"  ⏱️  Timeout after {timeout}s")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def find_iac_files(repo_path: Path) -> List[Path]:
    """
    Recursively find all IaC files in repository.
    """
    iac_files = []
    
    for root, dirs, files in os.walk(repo_path):
        # Skip common non-IaC directories
        dirs[:] = [d for d in dirs if d not in {
            '.git', 'node_modules', '.venv', 'venv', '__pycache__',
            '.pytest_cache', '.terraform', 'dist', 'build'
        }]
        
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in IAC_EXTENSIONS:
                iac_files.append(Path(root) / file)
    
    return iac_files

def copy_iac_files(iac_files: List[Path], repo_id: str, output_dir: Path) -> int:
    """
    Copy IaC files to output directory with repo-based organization.
    """
    repo_output = output_dir / repo_id
    repo_output.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    for src_file in iac_files:
        try:
            # Preserve relative structure within repo
            rel_path = src_file.relative_to(src_file.parents[len(src_file.parents) - 1])
            dest_file = repo_output / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_file, dest_file)
            copied += 1
        except Exception as e:
            print(f"    ⚠️  Failed to copy {src_file.name}: {e}")
    
    return copied

def restore_dataset(args):
    """
    Main restoration workflow.
    """
    print("\n" + "=" * 60)
    print("🔄 CloudGuard AI — Dataset Restoration")
    print("=" * 60 + "\n")
    
    # Setup
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dir = Path("temp_clones")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Get repository list
    repos = get_repo_list(args.repo_csv, args.start, args.limit)
    
    if not repos:
        print(f"❌ No repositories found in {args.repo_csv}")
        return
    
    print(f"📋 Repository Source: {args.repo_csv}")
    print(f"📁 Output Directory: {output_dir}")
    print(f"📊 Repositories to process: {len(repos)}")
    print(f"⏱️  Clone timeout: {args.clone_timeout}s\n")
    
    # Statistics
    stats = {
        'repos_attempted': 0,
        'repos_cloned': 0,
        'repos_with_iac': 0,
        'total_iac_files': 0,
        'failed_clones': []
    }
    
    start_time = time.time()
    
    # Process each repository
    for idx, (repo_id, repo_url) in enumerate(repos, 1):
        print(f"[{idx}/{len(repos)}] Processing: {repo_id}")
        print(f"  URL: {repo_url}")
        
        stats['repos_attempted'] += 1
        
        # Clone to temp location
        clone_path = temp_dir / repo_id
        
        # Skip if already exists in output (resume safety)
        if (output_dir / repo_id).exists():
            print(f"  ✅ Already processed (found in {args.output_dir})")
            existing_files = list((output_dir / repo_id).rglob('*'))
            stats['total_iac_files'] += len([f for f in existing_files if f.is_file()])
            stats['repos_with_iac'] += 1
            continue
        
        # Clean temp directory if exists
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)
        
        # Clone
        print("  📥 Cloning...", end=' ', flush=True)
        if not clone_repo(repo_url, clone_path, args.clone_timeout):
            print("❌ Failed")
            stats['failed_clones'].append((repo_id, repo_url))
            continue
        
        print("✅")
        stats['repos_cloned'] += 1
        
        # Find IaC files
        print("  🔍 Scanning for IaC files...", end=' ', flush=True)
        iac_files = find_iac_files(clone_path)
        print(f"{len(iac_files)} found")
        
        if iac_files:
            # Copy to output
            print("  📋 Copying IaC files...", end=' ', flush=True)
            copied = copy_iac_files(iac_files, repo_id, output_dir)
            print(f"✅ {copied} copied")
            
            stats['repos_with_iac'] += 1
            stats['total_iac_files'] += copied
        else:
            print("  ℹ️  No IaC files found")
        
        # Cleanup temp clone
        shutil.rmtree(clone_path, ignore_errors=True)
        
        # Progress update every 10 repos
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / idx
            remaining = (len(repos) - idx) * avg_time
            print(f"\n  ⏱️  Progress: {idx}/{len(repos)} | Elapsed: {elapsed:.1f}s | ETA: {remaining/60:.1f}min\n")
    
    # Cleanup temp directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Final summary
    elapsed_total = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("✅ Restoration Complete")
    print("=" * 60)
    print(f"\n📊 Statistics:")
    print(f"  Repositories attempted: {stats['repos_attempted']}")
    print(f"  Successfully cloned: {stats['repos_cloned']}")
    print(f"  Repos with IaC files: {stats['repos_with_iac']}")
    print(f"  Total IaC files extracted: {stats['total_iac_files']}")
    print(f"  Failed clones: {len(stats['failed_clones'])}")
    print(f"\n⏱️  Total time: {elapsed_total/60:.1f} minutes")
    print(f"📁 Output location: {output_dir.absolute()}\n")
    
    if stats['failed_clones']:
        print(f"⚠️  Failed repositories ({len(stats['failed_clones'])}):")
        for repo_id, url in stats['failed_clones'][:10]:
            print(f"  - {repo_id}: {url}")
        if len(stats['failed_clones']) > 10:
            print(f"  ... and {len(stats['failed_clones']) - 10} more")
    
    print()

if __name__ == '__main__':
    args = parse_args()
    restore_dataset(args)
