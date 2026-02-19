#!/usr/bin/env pwsh
# CloudGuardAI Deployment Script
# Usage: .\deploy.ps1 -Environment [local|staging|production]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('local','staging','production')]
    [string]$Environment = 'local',
    
    [switch]$Build = $false,
    [switch]$Push = $false,
    [string]$Registry = 'cloudguard'
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CloudGuardAI Deployment Script" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ImageTag = if ($Environment -eq 'production') { 'latest' } else { $Environment }

function Test-Prerequisites {
    Write-Host "`n[1/7] Checking prerequisites..." -ForegroundColor Yellow
    
    # Check Docker
    try {
        docker --version | Out-Null
        Write-Host "✓ Docker installed" -ForegroundColor Green
    } catch {
        Write-Host "✗ Docker not installed. Please install Docker Desktop." -ForegroundColor Red
        exit 1
    }
    
    if ($Environment -ne 'local') {
        # Check kubectl for K8s deployments
        try {
            kubectl version --client | Out-Null
            Write-Host "✓ kubectl installed" -ForegroundColor Green
        } catch {
            Write-Host "✗ kubectl not installed. Required for $Environment deployment." -ForegroundColor Red
            exit 1
        }
    }
}

function Build-Images {
    if (-not $Build) {
        Write-Host "`n[2/7] Skipping image build (use -Build to enable)" -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n[2/7] Building Docker images..." -ForegroundColor Yellow
    
    Push-Location $ProjectRoot
    
    # Build API image
    Write-Host "Building API image..." -ForegroundColor Cyan
    docker build -f infra/Dockerfile.api -t "$Registry/cloudguard-api:$ImageTag" .
    
    # Build ML service image
    Write-Host "Building ML service image..." -ForegroundColor Cyan
    docker build -f infra/Dockerfile.ml -t "$Registry/cloudguard-ml:$ImageTag" .
    
    # Build Web image
    Write-Host "Building Web image..." -ForegroundColor Cyan
    docker build -f infra/Dockerfile.web -t "$Registry/cloudguard-web:$ImageTag" .
    
    Pop-Location
    Write-Host "✓ All images built successfully" -ForegroundColor Green
}

function Push-Images {
    if (-not $Push) {
        Write-Host "`n[3/7] Skipping image push (use -Push to enable)" -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n[3/7] Pushing Docker images..." -ForegroundColor Yellow
    
    docker push "$Registry/cloudguard-api:$ImageTag"
    docker push "$Registry/cloudguard-ml:$ImageTag"
    docker push "$Registry/cloudguard-web:$ImageTag"
    
    Write-Host "✓ All images pushed successfully" -ForegroundColor Green
}

function Deploy-Local {
    Write-Host "`n[4/7] Deploying to local environment..." -ForegroundColor Yellow
    
    Push-Location "$ProjectRoot/infra"
    
    # Create .env if it doesn't exist
    if (-not (Test-Path ".env")) {
        Write-Host "Creating .env file from template..." -ForegroundColor Cyan
        Copy-Item ".env.example" ".env"
        Write-Host "⚠ Please update .env with your configuration" -ForegroundColor Yellow
    }
    
    # Start services
    docker-compose down
    docker-compose up -d --build
    
    # Wait for services to be healthy
    Write-Host "Waiting for services to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    # Run migrations
    Write-Host "Running database migrations..." -ForegroundColor Cyan
    docker-compose exec -T api alembic upgrade head
    
    Pop-Location
    
    Write-Host "✓ Local deployment complete" -ForegroundColor Green
    Write-Host "`nAccess the application at:" -ForegroundColor Cyan
    Write-Host "  Web UI:  http://localhost:3000" -ForegroundColor White
    Write-Host "  API:     http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
}

function Deploy-Kubernetes {
    param([string]$Env)
    
    Write-Host "`n[4/7] Deploying to Kubernetes ($Env)..." -ForegroundColor Yellow
    
    $namespace = "cloudguard-$Env"
    $k8sPath = "$ProjectRoot/infra/k8s"
    
    # Create namespace
    Write-Host "Creating namespace: $namespace" -ForegroundColor Cyan
    kubectl create namespace $namespace --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply manifests
    Write-Host "Applying Kubernetes manifests..." -ForegroundColor Cyan
    kubectl apply -f "$k8sPath/postgres.yaml" -n $namespace
    kubectl apply -f "$k8sPath/redis.yaml" -n $namespace
    
    # Wait for databases
    Write-Host "Waiting for databases to be ready..." -ForegroundColor Cyan
    kubectl wait --for=condition=ready pod -l app=postgres -n $namespace --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n $namespace --timeout=300s
    
    # Deploy services
    kubectl apply -f "$k8sPath/ml-service.yaml" -n $namespace
    kubectl apply -f "$k8sPath/api.yaml" -n $namespace
    kubectl apply -f "$k8sPath/worker.yaml" -n $namespace
    kubectl apply -f "$k8sPath/web.yaml" -n $namespace
    kubectl apply -f "$k8sPath/ingress.yaml" -n $namespace
    
    # Wait for deployments
    Write-Host "Waiting for deployments to be ready..." -ForegroundColor Cyan
    kubectl rollout status deployment/api -n $namespace
    kubectl rollout status deployment/ml-service -n $namespace
    kubectl rollout status deployment/web -n $namespace
    
    Write-Host "✓ Kubernetes deployment complete" -ForegroundColor Green
    
    # Show status
    Write-Host "`nDeployment status:" -ForegroundColor Cyan
    kubectl get pods -n $namespace
    kubectl get svc -n $namespace
    kubectl get ingress -n $namespace
}

function Run-HealthChecks {
    Write-Host "`n[5/7] Running health checks..." -ForegroundColor Yellow
    
    if ($Environment -eq 'local') {
        $apiUrl = "http://localhost:8000/health"
        $mlUrl = "http://localhost:8001/health"
        $webUrl = "http://localhost:3000"
        
        Start-Sleep -Seconds 5
        
        try {
            $apiHealth = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 10
            Write-Host "✓ API health check passed" -ForegroundColor Green
        } catch {
            Write-Host "✗ API health check failed" -ForegroundColor Red
        }
        
        try {
            $mlHealth = Invoke-RestMethod -Uri $mlUrl -TimeoutSec 10
            Write-Host "✓ ML service health check passed" -ForegroundColor Green
        } catch {
            Write-Host "✗ ML service health check failed" -ForegroundColor Red
        }
        
        try {
            $webHealth = Invoke-WebRequest -Uri $webUrl -TimeoutSec 10
            Write-Host "✓ Web UI health check passed" -ForegroundColor Green
        } catch {
            Write-Host "✗ Web UI health check failed" -ForegroundColor Red
        }
    }
}

function Show-Logs {
    Write-Host "`n[6/7] Recent logs:" -ForegroundColor Yellow
    
    if ($Environment -eq 'local') {
        Push-Location "$ProjectRoot/infra"
        docker-compose logs --tail=20
        Pop-Location
    } else {
        kubectl logs -n "cloudguard-$Environment" -l app=api --tail=20
    }
}

function Show-Summary {
    Write-Host "`n[7/7] Deployment Summary" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Environment: $Environment" -ForegroundColor White
    Write-Host "Status: ✓ Deployed" -ForegroundColor Green
    
    if ($Environment -eq 'local') {
        Write-Host "`nAccess URLs:" -ForegroundColor Cyan
        Write-Host "  Web UI:      http://localhost:3000" -ForegroundColor White
        Write-Host "  API:         http://localhost:8000" -ForegroundColor White
        Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor White
        Write-Host "  ML Service:  http://localhost:8001" -ForegroundColor White
        
        Write-Host "`nUseful Commands:" -ForegroundColor Cyan
        Write-Host "  View logs:   docker-compose -f infra/docker-compose.yml logs -f" -ForegroundColor White
        Write-Host "  Stop:        docker-compose -f infra/docker-compose.yml down" -ForegroundColor White
        Write-Host "  Restart:     docker-compose -f infra/docker-compose.yml restart" -ForegroundColor White
    } else {
        Write-Host "`nKubernetes Commands:" -ForegroundColor Cyan
        Write-Host "  View pods:   kubectl get pods -n cloudguard-$Environment" -ForegroundColor White
        Write-Host "  View logs:   kubectl logs -n cloudguard-$Environment -l app=api" -ForegroundColor White
        Write-Host "  Shell:       kubectl exec -it -n cloudguard-$Environment deployment/api -- /bin/bash" -ForegroundColor White
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
}

# Main execution
try {
    Test-Prerequisites
    Build-Images
    Push-Images
    
    if ($Environment -eq 'local') {
        Deploy-Local
    } else {
        Deploy-Kubernetes -Env $Environment
    }
    
    Run-HealthChecks
    Show-Logs
    Show-Summary
    
} catch {
    Write-Host "`n✗ Deployment failed: $_" -ForegroundColor Red
    exit 1
}
