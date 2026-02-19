# CloudGuard AI - Validation Environment Setup
# This script sets up the validation environment for Phase 6

Write-Host "`n===================================================================" -ForegroundColor Cyan
Write-Host "  CloudGuard AI - Validation Environment Setup" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan

$VALIDATION_DIR = "$PSScriptRoot"
$TERRAGOAT_DIR = "$VALIDATION_DIR\terragoat"
$RESULTS_DIR = "$VALIDATION_DIR\results"

# Create results directory
Write-Host "`n[1/5] Creating results directory..." -ForegroundColor Yellow
if (!(Test-Path $RESULTS_DIR)) {
    New-Item -ItemType Directory -Path $RESULTS_DIR | Out-Null
    Write-Host "   ✓ Created: $RESULTS_DIR" -ForegroundColor Green
} else {
    Write-Host "   ✓ Already exists: $RESULTS_DIR" -ForegroundColor Green
}

# Clone TerraGoat if not exists
Write-Host "`n[2/5] Setting up TerraGoat (deliberately vulnerable Terraform)..." -ForegroundColor Yellow
if (!(Test-Path $TERRAGOAT_DIR)) {
    Write-Host "   Cloning TerraGoat repository..." -ForegroundColor Gray
    git clone https://github.com/bridgecrewio/terragoat.git $TERRAGOAT_DIR
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ TerraGoat cloned successfully" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Failed to clone TerraGoat" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✓ TerraGoat already exists" -ForegroundColor Green
}

# Count Terraform files
$tfFiles = Get-ChildItem -Path $TERRAGOAT_DIR -Filter "*.tf" -Recurse | Where-Object { $_.FullName -notmatch ".terraform" }
Write-Host "   Found $($tfFiles.Count) Terraform files to test" -ForegroundColor Cyan

# Check Python dependencies
Write-Host "`n[3/5] Checking Python dependencies..." -ForegroundColor Yellow
$requiredPackages = @("requests", "sqlalchemy", "pydantic", "fastapi")
foreach ($package in $requiredPackages) {
    python -c "import $package" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ $package installed" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $package not installed - installing..." -ForegroundColor Yellow
        pip install $package -q
    }
}

# Check optional tools
Write-Host "`n[4/5] Checking comparison tools (optional)..." -ForegroundColor Yellow

# Check Checkov
$checkovInstalled = $false
try {
    checkov --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Checkov installed" -ForegroundColor Green
        $checkovInstalled = $true
    }
} catch {
    Write-Host "   ⚠  Checkov not installed (optional)" -ForegroundColor DarkGray
    Write-Host "      Install with: pip install checkov" -ForegroundColor DarkGray
}

# Check TFSec
$tfsecInstalled = $false
try {
    tfsec --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ TFSec installed" -ForegroundColor Green
        $tfsecInstalled = $true
    }
} catch {
    Write-Host "   ⚠  TFSec not installed (optional)" -ForegroundColor DarkGray
    Write-Host "      Download from: https://github.com/aquasecurity/tfsec/releases" -ForegroundColor DarkGray
}

# Check Terrascan
$terrascanInstalled = $false
try {
    terrascan version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Terrascan installed" -ForegroundColor Green
        $terrascanInstalled = $true
    }
} catch {
    Write-Host "   ⚠  Terrascan not installed (optional)" -ForegroundColor DarkGray
    Write-Host "      Download from: https://github.com/tenable/terrascan/releases" -ForegroundColor DarkGray
}

# Summary
Write-Host "`n[5/5] Setup Summary" -ForegroundColor Yellow
Write-Host "   ✓ Validation environment ready" -ForegroundColor Green
Write-Host "   ✓ TerraGoat: $($tfFiles.Count) files ready to scan" -ForegroundColor Green
Write-Host "   ✓ Python dependencies installed" -ForegroundColor Green

$toolCount = @($checkovInstalled, $tfsecInstalled, $terrascanInstalled).Where({ $_ }).Count
if ($toolCount -gt 0) {
    Write-Host "   ✓ Comparison tools: $toolCount/3 installed" -ForegroundColor Green
} else {
    Write-Host "   ⚠  Comparison tools: 0/3 installed (optional)" -ForegroundColor Yellow
}

# Next steps
Write-Host "`n===================================================================" -ForegroundColor Cyan
Write-Host "  ✓ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "===================================================================" -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Run CloudGuard AI validation test:" -ForegroundColor White
Write-Host "     python tests\validation\test_terragoat.py" -ForegroundColor Cyan
Write-Host "`n  2. Run tool comparison (if tools installed):" -ForegroundColor White
Write-Host "     python tests\validation\compare_tools.py" -ForegroundColor Cyan
Write-Host "`n  3. View results in:" -ForegroundColor White
Write-Host "     tests\validation\results\" -ForegroundColor Cyan

Write-Host "`n"
