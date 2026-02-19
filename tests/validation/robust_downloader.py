#!/usr/bin/env python3
"""
Production-Grade GitHub IaC Files Downloader

This script downloads ACTUAL IaC files from GitHub repositories with:
- GitHub token support for 5000 req/hour
- Exponential backoff for rate limits
- Resume capability
- Progress persistence
- Error recovery

Setup:
1. Create GitHub Personal Access Token: https://github.com/settings/tokens
2. Set environment variable: $env:GITHUB_TOKEN = "your_token_here"
3. Run this script
"""

import csv
import os
import sys
import json
import requests
import time
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pickle

class RobustGitHubDownloader:
    """Production-grade GitHub file downloader with rate limit handling"""
    
    def __init__(self, output_dir: str, cache_file: str = "download_progress.pkl"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = Path(__file__).parent / cache_file
        
        # GitHub authentication
        self.github_token = os.environ.get('GITHUB_TOKEN', None)
        if not self.github_token:
            print("\n⚠️  WARNING: No GITHUB_TOKEN found!")
            print("   Without token: 60 requests/hour (will take DAYS)")
            print("   With token: 5000 requests/hour (will take 2-4 hours)")
            print("\n   To set token:")
            print('   PowerShell: $env:GITHUB_TOKEN = "ghp_your_token_here"')
            print('   Linux/Mac: export GITHUB_TOKEN="ghp_your_token_here"')
            print("\n   Get token: https://github.com/settings/tokens")
            print("   Permissions needed: public_repo (read-only)")
            
            response = input("\n   Continue WITHOUT token? (yes/no): ").strip().lower()
            if response != 'yes':
                print("   Please set GITHUB_TOKEN and try again.")
                sys.exit(1)
        
        self.headers = {}
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
            print(f"✅ GitHub token configured (5000 req/hour limit)")
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Progress tracking
        self.downloaded_files = {}
        self.failed_downloads = {}
        self.repos_processed = set()
        self.load_progress()
        
        # Rate limit tracking
        self.requests_made = 0
        self.rate_limit_remaining = 5000 if self.github_token else 60
        self.rate_limit_reset_time = None
        
    def load_progress(self):
        """Load previous download progress"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.downloaded_files = data.get('downloaded', {})
                    self.failed_downloads = data.get('failed', {})
                    self.repos_processed = data.get('repos', set())
                    print(f"📂 Resumed: {len(self.downloaded_files)} files already downloaded")
            except Exception as e:
                print(f"⚠️  Could not load progress: {e}")
    
    def save_progress(self):
        """Save download progress"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'downloaded': self.downloaded_files,
                    'failed': self.failed_downloads,
                    'repos': self.repos_processed
                }, f)
        except Exception as e:
            print(f"⚠️  Could not save progress: {e}")
    
    def check_rate_limit(self):
        """Check and handle GitHub rate limits"""
        try:
            url = "https://api.github.com/rate_limit"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                core = data['resources']['core']
                self.rate_limit_remaining = core['remaining']
                self.rate_limit_reset_time = core['reset']
                
                if self.rate_limit_remaining < 100:
                    reset_time = datetime.fromtimestamp(self.rate_limit_reset_time)
                    wait_seconds = (reset_time - datetime.now()).total_seconds()
                    
                    if wait_seconds > 0:
                        print(f"\n⏳ Rate limit low ({self.rate_limit_remaining} remaining)")
                        print(f"   Waiting {wait_seconds/60:.1f} minutes until reset...")
                        time.sleep(wait_seconds + 10)
                        self.check_rate_limit()
        except Exception as e:
            print(f"⚠️  Rate limit check failed: {e}")
    
    def download_file_with_retry(self, owner: str, repo: str, path: str, max_retries: int = 3) -> Optional[str]:
        """Download file content with exponential backoff"""
        
        # Check if already downloaded
        file_key = f"{owner}/{repo}/{path}"
        if file_key in self.downloaded_files:
            return self.downloaded_files[file_key]
        
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        for attempt in range(max_retries):
            try:
                # Check rate limit before request
                if self.rate_limit_remaining < 10:
                    self.check_rate_limit()
                
                response = self.session.get(url, timeout=30)
                self.requests_made += 1
                self.rate_limit_remaining -= 1
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle file (not directory)
                    if isinstance(data, dict) and 'content' in data:
                        content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                        
                        # Save to disk
                        safe_name = f"{owner}_{repo}_{path.replace('/', '_')}"
                        local_path = self.output_dir / safe_name
                        
                        with open(local_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # Cache success
                        self.downloaded_files[file_key] = str(local_path)
                        return str(local_path)
                
                elif response.status_code == 403:
                    # Rate limit hit
                    print(f"   ⏳ Rate limit hit, checking...")
                    self.check_rate_limit()
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
                elif response.status_code == 404:
                    # File not found (may have been deleted)
                    self.failed_downloads[file_key] = "404 Not Found"
                    return None
                    
                else:
                    # Other error
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        self.failed_downloads[file_key] = f"HTTP {response.status_code}"
                        return None
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.failed_downloads[file_key] = str(e)
                    return None
        
        return None
    
    def download_from_repos_csv(self, csv_path: str, target_files: int = 5000):
        """Download files from repositories CSV"""
        
        print(f"\n{'='*80}")
        print(f"DOWNLOADING {target_files} IaC FILES FROM GITHUB")
        print(f"{'='*80}")
        print(f"Source: {csv_path}")
        print(f"Target: {target_files} files")
        print(f"Output: {self.output_dir}")
        print(f"Already downloaded: {len(self.downloaded_files)}")
        print(f"{'='*80}\n")
        
        files_needed = target_files - len(self.downloaded_files)
        if files_needed <= 0:
            print(f"✅ Already have {len(self.downloaded_files)} files!")
            return
        
        repos_processed_count = len(self.repos_processed)
        files_downloaded_this_session = 0
        
        start_time = time.time()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if len(self.downloaded_files) >= target_files:
                    break
                
                url = row.get('url', '')
                programs_str = row.get('programs', '')
                
                if not url or not programs_str or programs_str == 'nan':
                    continue
                
                # Parse repository
                try:
                    parts = url.replace('https://api.github.com/repos/', '').split('/')
                    if len(parts) < 2:
                        continue
                    owner, repo = parts[0], parts[1]
                    repo_key = f"{owner}/{repo}"
                    
                    # Skip if already processed
                    if repo_key in self.repos_processed:
                        continue
                    
                    repos_processed_count += 1
                    
                    # Parse programs list
                    import ast
                    programs = ast.literal_eval(programs_str)
                    if not isinstance(programs, list):
                        continue
                    
                    print(f"\n[{repos_processed_count}] {owner}/{repo} ({len(programs)} files)")
                    
                    # Download files from this repo
                    repo_downloads = 0
                    for program_path in programs:
                        if len(self.downloaded_files) >= target_files:
                            break
                        
                        result = self.download_file_with_retry(owner, repo, program_path)
                        
                        if result:
                            repo_downloads += 1
                            files_downloaded_this_session += 1
                            print(f"  ✓ {program_path} ({len(self.downloaded_files)}/{target_files})")
                        
                        # Respect rate limits (small delay between files)
                        time.sleep(0.1)
                    
                    # Mark repo as processed
                    self.repos_processed.add(repo_key)
                    
                    # Save progress every 10 repos
                    if repos_processed_count % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = files_downloaded_this_session / elapsed if elapsed > 0 else 0
                        remaining = target_files - len(self.downloaded_files)
                        eta_seconds = remaining / rate if rate > 0 else 0
                        
                        print(f"\n📊 Progress Update:")
                        print(f"   Files: {len(self.downloaded_files)}/{target_files}")
                        print(f"   Repos: {repos_processed_count}")
                        print(f"   Failed: {len(self.failed_downloads)}")
                        print(f"   Rate: {rate:.1f} files/min")
                        print(f"   ETA: {eta_seconds/60:.0f} minutes")
                        print(f"   API calls: {self.requests_made}, Remaining: {self.rate_limit_remaining}")
                        
                        self.save_progress()
                
                except Exception as e:
                    print(f"   ✗ Error processing repo: {e}")
                    continue
        
        # Final save
        self.save_progress()
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"DOWNLOAD COMPLETE!")
        print(f"{'='*80}")
        print(f"✅ Total files downloaded: {len(self.downloaded_files)}")
        print(f"✅ New files this session: {files_downloaded_this_session}")
        print(f"⚠️  Failed downloads: {len(self.failed_downloads)}")
        print(f"📁 Repos processed: {repos_processed_count}")
        print(f"⏱️  Time elapsed: {elapsed/60:.1f} minutes")
        print(f"📊 Download rate: {files_downloaded_this_session/(elapsed/60):.1f} files/minute")
        print(f"{'='*80}\n")
        
        return {
            'total_downloaded': len(self.downloaded_files),
            'new_this_session': files_downloaded_this_session,
            'failed': len(self.failed_downloads),
            'repos_processed': repos_processed_count,
            'elapsed_minutes': elapsed / 60
        }


def main():
    """Main execution"""
    
    # Configuration
    data_dir = Path(__file__).parent.parent.parent / "data"
    repos_csv = data_dir / "datasets" / "repositories.csv"
    output_dir = data_dir / "downloaded_21k_files"
    
    if not repos_csv.exists():
        print(f"❌ Error: {repos_csv} not found!")
        return
    
    # Create downloader
    downloader = RobustGitHubDownloader(str(output_dir))
    
    # Set target (start with 5000, can increase)
    target_files = 5000
    
    print("\n" + "="*80)
    print("GITHUB IAC FILES DOWNLOADER - PRODUCTION MODE")
    print("="*80)
    print("\nThis will download REAL IaC files from GitHub.")
    print(f"Target: {target_files} files")
    print(f"Estimated time with token: 2-4 hours")
    print(f"Estimated time without token: 2-3 DAYS")
    print("="*80)
    
    # Start download
    results = downloader.download_from_repos_csv(str(repos_csv), target_files)
    
    if results and results['total_downloaded'] > 0:
        print("\n✅ Ready to scan!")
        print(f"   Files downloaded: {results['total_downloaded']}")
        print(f"   Location: {output_dir}")
        print(f"\nNext step: Run the scanner on downloaded files")


if __name__ == "__main__":
    main()
