#!/usr/bin/env pwsh
# CloudGuard AI - Quick Start Script (No Docker Required)
# Runs the application locally with all AI models

param(
    [switch]$InstallDeps = $false,
    [switch]$RunTests = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CloudGuard AI - Local Development Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ProjectRoot = $PSScriptRoot

# Check Python
Write-Host "`n[1/5] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Install Dependencies
if ($InstallDeps) {
    Write-Host "`n[2/5] Installing dependencies..." -ForegroundColor Yellow
    
    # API dependencies
    Write-Host "Installing API dependencies..." -ForegroundColor Cyan
    Push-Location "$ProjectRoot/api"
    pip install -r requirements.txt
    Pop-Location
    
    # ML dependencies
    Write-Host "Installing ML dependencies..." -ForegroundColor Cyan
    Push-Location "$ProjectRoot/ml"
    pip install -r requirements.txt
    Pop-Location
    
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "`n[2/5] Skipping dependency installation (use -InstallDeps)" -ForegroundColor Yellow
}

# Verify AI Models
Write-Host "`n[3/5] Verifying AI models..." -ForegroundColor Yellow

$gnnModel = "$ProjectRoot/ml/models_artifacts/gnn_attack_detector.pt"
$rlModel = "$ProjectRoot/ml/models_artifacts/rl_auto_fix_agent.pt"
$transformerImpl = "$ProjectRoot/ml/models/transformer_code_gen.py"

if (Test-Path $gnnModel) {
    Write-Host "✓ GNN model found: $gnnModel" -ForegroundColor Green
} else {
    Write-Host "✗ GNN model missing!" -ForegroundColor Red
}

if (Test-Path $rlModel) {
    Write-Host "✓ RL model found: $rlModel" -ForegroundColor Green
} else {
    Write-Host "✗ RL model missing!" -ForegroundColor Red
}

if (Test-Path $transformerImpl) {
    Write-Host "✓ Transformer implementation found" -ForegroundColor Green
} else {
    Write-Host "✗ Transformer implementation missing!" -ForegroundColor Red
}

# Run Tests
if ($RunTests) {
    Write-Host "`n[4/5] Running verification tests..." -ForegroundColor Yellow
    Push-Location $ProjectRoot
    python -m pytest tests/ -q --tb=short
    Pop-Location
} else {
    Write-Host "`n[4/5] Skipping tests (use -RunTests)" -ForegroundColor Yellow
}

# Start Services
Write-Host "`n[5/5] Starting services..." -ForegroundColor Yellow
Write-Host "Choose an option:" -ForegroundColor Cyan
Write-Host "  1. Start API only (port 8000)" -ForegroundColor White
Write-Host "  2. Start ML service only (port 8001)" -ForegroundColor White
Write-Host "  3. Start both services" -ForegroundColor White
Write-Host "  4. Run integration test" -ForegroundColor White
Write-Host "  5. Exit" -ForegroundColor White

$choice = Read-Host "`nEnter choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`nStarting API server..." -ForegroundColor Cyan
        Write-Host "Access at: http://localhost:8000/docs" -ForegroundColor Green
        Push-Location "$ProjectRoot/api"
        $env:PYTHONPATH = $ProjectRoot
        uvicorn app.main:app --reload --port 8000
        Pop-Location
    }
    "2" {
        Write-Host "`nStarting ML service..." -ForegroundColor Cyan
        Write-Host "Access at: http://localhost:8001/health" -ForegroundColor Green
        Push-Location "$ProjectRoot/ml"
        $env:PYTHONPATH = $ProjectRoot
        uvicorn ml_service.main:app --reload --port 8001
        Pop-Location
    }
    "3" {
        Write-Host "`nStarting both services..." -ForegroundColor Cyan
        Write-Host "API: http://localhost:8000/docs" -ForegroundColor Green
        Write-Host "ML:  http://localhost:8001/health" -ForegroundColor Green
        Write-Host "`n⚠ Press Ctrl+C to stop" -ForegroundColor Yellow
        
        # Start API in background
        $apiJob = Start-Job -ScriptBlock {
            param($root)
            cd "$root/api"
            $env:PYTHONPATH = $root
            uvicorn app.main:app --reload --port 8000
        } -ArgumentList $ProjectRoot
        
        # Start ML service in foreground
        Push-Location "$ProjectRoot/ml"
        $env:PYTHONPATH = $ProjectRoot
        try {
            uvicorn ml_service.main:app --reload --port 8001
        } finally {
            Stop-Job $apiJob -ErrorAction SilentlyContinue
            Remove-Job $apiJob -ErrorAction SilentlyContinue
            Pop-Location
        }
    }
    "4" {
        Write-Host "`nRunning full test suite..." -ForegroundColor Cyan
        Push-Location $ProjectRoot
        python -m pytest tests/ -v --tb=short
        Pop-Location
    }
    default {
        Write-Host "`nExiting..." -ForegroundColor Yellow
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CloudGuard AI Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
