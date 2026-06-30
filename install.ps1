# Afia Clinic - Smart Windows Installer
# Supports: Docker Desktop or Native Odoo 18 CE
# Usage: Right-click -> Run with PowerShell (as Administrator)

Write-Host ""
Write-Host "  Afia Clinic - Installer" -ForegroundColor Cyan
Write-Host "  ITCS (IT Corner Solutions)" -ForegroundColor Gray
Write-Host "  itcornersolutions.net" -ForegroundColor Gray
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$modulesDir = Join-Path $scriptDir "modules"

# ── Detect Docker ─────────────────────────────────────────────────────────────
$dockerAvailable = $false
try {
    $dockerVersion = & docker --version 2>$null
    if ($LASTEXITCODE -eq 0) { $dockerAvailable = $true }
} catch {}

# ── Detect Native Odoo ────────────────────────────────────────────────────────
$odooService = Get-Service -Name "*odoo*" -ErrorAction SilentlyContinue | Select-Object -First 1
$customAddons = $null
$searchPaths = @(
    "C:\Program Files\Odoo 18.0*\server\custom_addons",
    "C:\Program Files (x86)\Odoo 18.0*\server\custom_addons"
)
foreach ($pattern in $searchPaths) {
    $found = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $customAddons = $found.FullName; break }
}

# ── Decision ──────────────────────────────────────────────────────────────────
if ($dockerAvailable) {
    Write-Host "  [DETECTED] Docker available - using Docker install" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Starting Afia Clinic stack..." -ForegroundColor Cyan
    Set-Location (Join-Path $scriptDir "docker")
    & docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: docker compose failed. Check Docker Desktop is running." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    Write-Host "  Waiting for Odoo to start (30 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    Write-Host ""
    Write-Host "  Done! Open your browser and go to:" -ForegroundColor Green
    Write-Host "  http://localhost:8069" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Create a new database, then go to Apps and install 'Dental Hospital'." -ForegroundColor Gray
    Write-Host "  All 38 Afia Clinic modules will be available." -ForegroundColor Gray

} elseif ($customAddons -and $odooService) {
    Write-Host "  [DETECTED] Odoo 18 CE installed - using native install" -ForegroundColor Green
    Write-Host "  Target: $customAddons" -ForegroundColor Gray
    Write-Host ""

    # Copy modules
    $count = 0
    Get-ChildItem -Path $modulesDir -Directory | ForEach-Object {
        $dest = Join-Path $customAddons $_.Name
        Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
        $count++
    }
    Write-Host "  Copied $count modules to custom_addons" -ForegroundColor Green

    # Restart Odoo service
    Write-Host "  Restarting Odoo service..." -ForegroundColor Yellow
    Restart-Service -Name $odooService.Name -Force
    Write-Host "  Waiting for Odoo to start (20 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20

    Write-Host ""
    Write-Host "  Done! Open your browser and go to:" -ForegroundColor Green
    Write-Host "  http://localhost:8069" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Go to Apps > Update Apps List, then install 'Dental Hospital'." -ForegroundColor Gray
    Write-Host "  All 38 Afia Clinic modules will be available." -ForegroundColor Gray

} else {
    Write-Host "  [NOT FOUND] Neither Docker nor Odoo 18 CE detected." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Choose one of:" -ForegroundColor Yellow
    Write-Host "  Option A (Recommended): Install Docker Desktop from https://docker.com/products/docker-desktop" -ForegroundColor Cyan
    Write-Host "                          Then re-run this script." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Option B: Install Odoo 18 CE from https://www.odoo.com/page/download" -ForegroundColor Cyan
    Write-Host "            Then re-run this script." -ForegroundColor Gray
}

Write-Host ""
