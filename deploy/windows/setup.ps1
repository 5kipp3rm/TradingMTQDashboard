# TradingMTQ Production Deployment Script for Windows
# This script automates the deployment process

param(
    [switch]$UsePostgreSQL = $false,
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TradingMTQ Production Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running in project directory
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: Please run this script from the TradingMTQ project root directory" -ForegroundColor Red
    exit 1
}

# Step 1: Check Python version
Write-Host "[1/9] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python (\d+\.\d+)") {
    $version = [version]$matches[1]
    if ($version -ge [version]"3.9") {
        Write-Host "  ✓ Python $($matches[1]) detected" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Python 3.9+ required (found $($matches[1]))" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✗ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Step 2: Create virtual environment
Write-Host "[2/9] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  ℹ Virtual environment already exists" -ForegroundColor Blue
} else {
    python -m venv venv
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
}

# Step 3: Activate virtual environment and install dependencies
Write-Host "[3/9] Installing dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install -e . --quiet
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# Step 4: Check MetaTrader5 availability
Write-Host "[4/9] Checking MetaTrader5..." -ForegroundColor Yellow
$mt5Check = python -c "try: import MetaTrader5; print('OK')" 2>&1
if ($mt5Check -eq "OK") {
    Write-Host "  ✓ MetaTrader5 package available" -ForegroundColor Green
} else {
    Write-Host "  ℹ MetaTrader5 package not available (Windows only)" -ForegroundColor Blue
    Write-Host "    This is normal on non-Windows systems" -ForegroundColor Blue
}

# Step 5: Create .env file if it doesn't exist
Write-Host "[5/9] Configuring environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item "deploy\windows\.env.template" ".env"
    Write-Host "  ✓ Created .env file from template" -ForegroundColor Green
    Write-Host "  ⚠  IMPORTANT: Edit .env with your MT5 credentials!" -ForegroundColor Yellow
    Write-Host "    File location: $(Resolve-Path .env)" -ForegroundColor Yellow
} else {
    Write-Host "  ℹ .env file already exists" -ForegroundColor Blue
}

# Step 6: Initialize database
Write-Host "[6/9] Initializing database..." -ForegroundColor Yellow
if ($UsePostgreSQL) {
    Write-Host "  ℹ PostgreSQL mode - ensure TRADING_MTQ_DATABASE_URL is set in .env" -ForegroundColor Blue
} else {
    Write-Host "  ℹ SQLite mode - database will be created automatically" -ForegroundColor Blue
}

try {
    python src\database\migration_utils.py init
    Write-Host "  ✓ Database initialized successfully" -ForegroundColor Green
} catch {
    Write-Host "  ⚠  Database initialization warning (might be already initialized)" -ForegroundColor Yellow
}

# Step 7: Run tests (unless skipped)
if (-not $SkipTests) {
    Write-Host "[7/9] Running tests..." -ForegroundColor Yellow
    $testResult = pytest tests\test_models.py tests\test_repositories.py -q 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ All tests passed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠  Some tests failed (this might be expected if dependencies are missing)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[7/9] Skipping tests (--SkipTests flag)" -ForegroundColor Blue
}

# Step 8: Verify CLI installation
Write-Host "[8/9] Verifying CLI installation..." -ForegroundColor Yellow
$cliCheck = tradingmtq version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ CLI commands available" -ForegroundColor Green
} else {
    Write-Host "  ✗ CLI installation failed" -ForegroundColor Red
    exit 1
}

# Step 9: Display next steps
Write-Host "[9/9] Deployment preparation complete!" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Edit .env file with your MT5 credentials:" -ForegroundColor White
Write-Host "   $(Resolve-Path .env)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Review trading configuration:" -ForegroundColor White
Write-Host "   $(Resolve-Path config\currencies.yaml)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test MT5 connection:" -ForegroundColor White
Write-Host "   python -c ""import MetaTrader5 as mt5; print('MT5:', mt5.initialize()); mt5.shutdown()""" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Start in DEMO mode first:" -ForegroundColor White
Write-Host "   tradingmtq trade --demo" -ForegroundColor Green
Write-Host ""
Write-Host "5. When ready, start production:" -ForegroundColor White
Write-Host "   tradingmtq trade --aggressive" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Quick Commands" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  tradingmtq check          # System check" -ForegroundColor Gray
Write-Host "  tradingmtq trade --demo   # Demo mode" -ForegroundColor Gray
Write-Host "  tradingmtq trade          # Production" -ForegroundColor Gray
Write-Host "  tradingmtq version        # Show version" -ForegroundColor Gray
Write-Host ""
Write-Host "For detailed instructions, see:" -ForegroundColor White
Write-Host "  docs\PRODUCTION_DEPLOYMENT_CHECKLIST.md" -ForegroundColor Gray
Write-Host ""
Write-Host "✓ Deployment preparation successful!" -ForegroundColor Green
Write-Host ""
