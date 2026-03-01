# .github/hooks/setup.ps1
# Windows equivalent of setup.sh
$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = Get-Location }

Write-Host "🔧 metrics-dashboard session setup..."

# Backend
$backend = Join-Path $repoRoot "backend"
if (Test-Path (Join-Path $backend "requirements.txt")) {
    Write-Host "  → Installing Python dependencies..."
    pip install -r (Join-Path $backend "requirements.txt") --quiet --disable-pip-version-check
    Write-Host "  ✅ Backend dependencies ready"
}

# Frontend
$frontend = Join-Path $repoRoot "frontend"
if (Test-Path (Join-Path $frontend "package.json")) {
    Write-Host "  → Installing Node dependencies..."
    Push-Location $frontend
    npm install --silent
    Pop-Location
    Write-Host "  ✅ Frontend dependencies ready"
}

Write-Host "✅ Setup complete — agent is ready"
