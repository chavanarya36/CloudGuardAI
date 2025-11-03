Param(
    [string]$Labels = "labels_artifacts/iac_labels_clean.csv",
    [string]$IacRoot = "iac_subset",
    [string]$OutDir = "real_test_samples",
    [int]$MaxScan = 20000,
    [int]$MaxSizeBytes = 1000000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$path){
    if(-not [string]::IsNullOrWhiteSpace($path)){
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

$wsRoot = (Resolve-Path ".").Path
$iacBase = Join-Path $wsRoot $IacRoot
Ensure-Dir $iacBase
Ensure-Dir $OutDir

if(-not (Test-Path -LiteralPath $Labels)){
    throw "Labels CSV not found at '$Labels'"
}

Write-Host "Loading labels from: $Labels" -ForegroundColor Cyan
$rows = Import-Csv -LiteralPath $Labels
if(-not $rows){ throw "No rows in labels CSV: $Labels" }

function Try-ResolveLocal([object]$r){
    # 1) abs_path
    if($r.abs_path){
        $p = $r.abs_path -replace '/', '\\'
        if(Test-Path -LiteralPath $p){ return (Resolve-Path -LiteralPath $p).Path }
    }
    # 2) repo_root + rel_path
    if($r.repo_root -and $r.rel_path){
        $p2 = Join-Path ($r.repo_root -replace '/', '\\') ($r.rel_path -replace '/', '\\')
        if(Test-Path -LiteralPath $p2){ return (Resolve-Path -LiteralPath $p2).Path }
    }
    # 3) workspace iac_root + rel_path
    if($r.rel_path){
        $p3 = Join-Path $iacBase ($r.rel_path -replace '/', '\\')
        if(Test-Path -LiteralPath $p3){ return (Resolve-Path -LiteralPath $p3).Path }
    }
    return $null
}

function Try-DownloadFromGitHub([object]$r){
    if(-not $r.rel_path){ return $null }
    $rel = $r.rel_path -replace '^\\+','' -replace '^/+',''
    $parts = $rel -split '[\\/]'
    if($parts.Count -lt 2){ return $null }
    $repoDir = $parts[0]
    $innerPath = ($parts | Select-Object -Skip 1) -join '/'
    # Heuristic: repoDir is "owner_repo"
    if($repoDir -notmatch '^(?<owner>[^_]+)_(?<repo>.+)$'){
        return $null
    }
    $owner = $Matches['owner']
    $repo  = $Matches['repo']
    $branches = @('main','master','trunk','dev','develop','development','release','staging')
    foreach($br in $branches){
        $url = "https://raw.githubusercontent.com/$owner/$repo/$br/$innerPath"
        try{
            $dest = Join-Path $iacBase ($rel -replace '/', '\\')
            Ensure-Dir ([System.IO.Path]::GetDirectoryName($dest))
            Invoke-WebRequest -Uri $url -UseBasicParsing -OutFile $dest -ErrorAction Stop | Out-Null
            if((Test-Path -LiteralPath $dest) -and ((Get-Item -LiteralPath $dest).Length -gt 0)){
                Write-Host "Downloaded: $url -> $dest" -ForegroundColor Green
                return (Resolve-Path -LiteralPath $dest).Path
            }
        } catch {
            # try next branch
            continue
        }
    }
    return $null
}

function Select-Sample([object[]]$allRows, [bool]$wantPositive){
    $count = 0
    foreach($r in $allRows){
        if($count -ge $MaxScan){ break }
        $count++
        $label = $r.has_findings
        $isPos = ($label -in @('1',1,$true))
        if($isPos -ne $wantPositive){ continue }
        # Skip huge files
        $size = 0
        if([int]::TryParse([string]$r.size_bytes, [ref]$size)){
            if($size -gt $MaxSizeBytes){ continue }
        }
        # Prefer IaC-like extensions
        $ext = ([string]$r.ext).ToLowerInvariant()
        $okExt = @('.tf','.yaml','.yml','.json','.template','.bicep')
        if(($okExt -notcontains $ext) -and $ext){ continue }

        $p = Try-ResolveLocal $r
        if(-not $p){ $p = Try-DownloadFromGitHub $r }
        if($p){ return @{ row = $r; path = $p } }
    }
    return $null
}

Write-Host "Searching for a POSITIVE sample (has_findings=1)..." -ForegroundColor Cyan
$pos = Select-Sample -allRows $rows -wantPositive $true
if(-not $pos){ Write-Warning "Could not locate or download a positive sample within scan limit $MaxScan" }

Write-Host "Searching for a NEGATIVE sample (has_findings=0)..." -ForegroundColor Cyan
$neg = $null

# If we found a positive, try to find a negative in the same repository first for higher success rate
if($pos -and $pos.row){
    $posRel = [string]$pos.row.rel_path
    $repoDir = $null
    if($posRel){
        $posRel = $posRel -replace '^\\+','' -replace '^/+',''
        $repoDir = ($posRel -split '[\\/]')[0]
    }
    if($repoDir){
        Write-Host "Trying to find NEGATIVE in same repo: $repoDir" -ForegroundColor Yellow
        $sameRepoNegs = $rows | Where-Object { $_.has_findings -in @('0',0,$false) -and [string]$_.rel_path -like "$repoDir/*" }
        foreach($r in $sameRepoNegs){
            # Size and ext filters
            $size = 0
            if([int]::TryParse([string]$r.size_bytes, [ref]$size)){
                if($size -gt $MaxSizeBytes){ continue }
            }
            $ext = ([string]$r.ext).ToLowerInvariant()
            $okExt = @('.tf','.yaml','.yml','.json','.template','.bicep')
            if(($okExt -notcontains $ext) -and $ext){ continue }

            $p = Try-ResolveLocal $r
            if(-not $p){ $p = Try-DownloadFromGitHub $r }
            if($p){ $neg = @{ row = $r; path = $p }; break }
        }
    }
}

# Fallback: global search for any negative
if(-not $neg){
    $neg = Select-Sample -allRows $rows -wantPositive $false
}
if(-not $neg){ Write-Warning "Could not locate or download a negative sample within scan limit $MaxScan" }

$copied = @()
function Copy-ToOut([string]$src){
    $name = [System.IO.Path]::GetFileName($src)
    $dst = Join-Path $OutDir $name
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $copied += (Resolve-Path -LiteralPath $dst).Path
}

if($pos -and $pos.path){ Copy-ToOut $pos.path }
if($neg -and $neg.path){ Copy-ToOut $neg.path }

# Offline fallback: if negative still missing, synthesize a minimal safe file in the same repo
if(($null -eq $neg -or -not $neg.path) -and $pos -and $pos.row){
    Write-Warning "Negative sample not found online; creating a minimal fallback file locally."
    $posRel = [string]$pos.row.rel_path
    $repoDir = $null
    if($posRel){
        $posRel = $posRel -replace '^\\+','' -replace '^/+',''
        $repoDir = ($posRel -split '[\\/]')[0]
    }
    # Find a negative row path to mirror structure
    $negRow = $rows | Where-Object { $_.has_findings -in @('0',0,$false) -and [string]$_.rel_path -like "$repoDir/*" } | Select-Object -First 1
    if(-not $negRow){ $negRow = $rows | Where-Object { $_.has_findings -in @('0',0,$false) } | Select-Object -First 1 }
    if($negRow){
        $negRel = [string]$negRow.rel_path
        $target = Join-Path $iacBase ($negRel -replace '/', '\\')
        Ensure-Dir ([System.IO.Path]::GetDirectoryName($target))
                $ext = ([string]$negRow.ext).ToLowerInvariant()
                $lines = @()
                switch ($ext) {
                    '.tf' {
                        $lines = @(
                            '# fallback',
                            'terraform {',
                            '  required_version = ">= 0.12.0"',
                            '}'
                        )
                    }
                    '.yaml' { $lines = @('# fallback minimal YAML','name: noop') }
                    '.yml'  { $lines = @('# fallback minimal YAML','name: noop') }
                    '.json' { $lines = @('{}') }
                    '.bicep'{ $lines = @('// fallback minimal bicep') }
                    default { $lines = @('# fallback') }
                }
                Set-Content -LiteralPath $target -Value $lines -Encoding UTF8
        if(Test-Path -LiteralPath $target){
            Write-Host "Created fallback negative file: $target" -ForegroundColor Yellow
            Copy-ToOut $target
        }
    }
}

if($copied.Count -gt 0){
    $zip = "$OutDir.zip"
    if(Test-Path -LiteralPath $zip){ Remove-Item -LiteralPath $zip -Force }
    Compress-Archive -Path (Join-Path $OutDir '*') -DestinationPath $zip -Force
    Write-Host "Prepared samples:" -ForegroundColor Green
    $copied | ForEach-Object { Write-Host " - $_" }
    Write-Host ("ZIP: " + (Resolve-Path -LiteralPath $zip).Path) -ForegroundColor Green
} else {
    Write-Warning "Failed to prepare any samples. Provide the dataset base path or enable network access to GitHub."
}
