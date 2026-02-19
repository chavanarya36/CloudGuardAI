# GitHub Token Setup Guide

## Quick Setup (5 minutes)

### Step 1: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: `CloudGuard-IaC-Download`
4. Expiration: 30 days
5. Scopes: **Only check `public_repo`** (read access to public repos)
6. Click "Generate token"
7. **COPY THE TOKEN** (you won't see it again!)

### Step 2: Set Environment Variable

**PowerShell (Windows)**:
```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"
```

**To verify**:
```powershell
echo $env:GITHUB_TOKEN
```

**Linux/Mac**:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### Step 3: Run Downloader
```powershell
cd d:\CloudGuardAI\tests\validation
python robust_downloader.py
```

---

## Rate Limits

| Authentication | Requests/Hour | Time for 5000 Files |
|----------------|---------------|---------------------|
| **No Token** | 60 | ~83 hours (3.5 days) ❌ |
| **With Token** | 5,000 | ~2-4 hours ✅ |

---

## Estimated Timeline

### With GitHub Token (RECOMMENDED):
```
Step 1: Download 5000 files → 2-4 hours
Step 2: Scan files          → 15-30 minutes  
Step 3: Generate report     → 1 minute
────────────────────────────────────────
Total: 2.5-4.5 hours ✅
```

### Without Token (NOT RECOMMENDED):
```
Step 1: Download 5000 files → 3-4 DAYS ❌
(Will likely hit other issues)
```

---

## Troubleshooting

### "403 Rate limit exceeded"
- **With token**: Wait 1 hour, script will auto-resume
- **Without token**: Set GITHUB_TOKEN (see above)

### "401 Unauthorized"
- Token expired: Create new token
- Token invalid: Check you copied it correctly

### Script crashed
- No problem! Run again - it will resume from where it stopped
- Progress saved in `download_progress.pkl`

---

## Quick Start Commands

```powershell
# Set token (PASTE YOUR ACTUAL TOKEN)
$env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxxx"

# Verify token is set
echo $env:GITHUB_TOKEN

# Start download (will take 2-4 hours)
cd d:\CloudGuardAI\tests\validation
python robust_downloader.py

# After download completes, scan files  
python scan_real_files.py
```

---

**IMPORTANT**: 
- Do this NOW if you want results in 4 days
- With token: Complete in ~4 hours
- Without token: Takes 3-4 DAYS (not feasible)
