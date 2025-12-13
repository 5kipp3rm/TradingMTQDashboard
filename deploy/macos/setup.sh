#!/bin/bash
# TradingMTQ Development/Testing Setup Script for macOS/Linux
# Note: MetaTrader5 is Windows-only, this is for development and testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Options
SKIP_TESTS=false
USE_POSTGRESQL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --use-postgresql)
            USE_POSTGRESQL=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--skip-tests] [--use-postgresql]"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  TradingMTQ Development Setup${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if running in project directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}ERROR: Please run this script from the TradingMTQ project root directory${NC}"
    exit 1
fi

# Step 1: Check Python version
echo -e "${YELLOW}[1/9] Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    REQUIRED_VERSION="3.9"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        echo -e "${GREEN}  ✓ Python $PYTHON_VERSION detected${NC}"
        PYTHON_CMD=python3
    else
        echo -e "${RED}  ✗ Python 3.9+ required (found $PYTHON_VERSION)${NC}"
        exit 1
    fi
else
    echo -e "${RED}  ✗ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

# Step 2: Create virtual environment
echo -e "${YELLOW}[2/9] Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${BLUE}  ℹ Virtual environment already exists${NC}"
else
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}  ✓ Virtual environment created${NC}"
fi

# Step 3: Activate virtual environment and install dependencies
echo -e "${YELLOW}[3/9] Installing dependencies...${NC}"
source venv/bin/activate
$PYTHON_CMD -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install -e . --quiet
echo -e "${GREEN}  ✓ Dependencies installed${NC}"

# Step 4: Check MetaTrader5 availability
echo -e "${YELLOW}[4/9] Checking MetaTrader5...${NC}"
MT5_CHECK=$($PYTHON_CMD -c "try: import MetaTrader5; print('OK')" 2>&1 || echo "FAIL")
if [ "$MT5_CHECK" = "OK" ]; then
    echo -e "${GREEN}  ✓ MetaTrader5 package available${NC}"
else
    echo -e "${BLUE}  ℹ MetaTrader5 not available (Windows only)${NC}"
    echo -e "${BLUE}    This is expected on macOS/Linux${NC}"
    echo -e "${BLUE}    You can test the database layer and run unit tests${NC}"
fi

# Step 5: Create .env file if it doesn't exist
echo -e "${YELLOW}[5/9] Configuring environment...${NC}"
if [ ! -f ".env" ]; then
    cp deploy/macos/.env.template .env
    echo -e "${GREEN}  ✓ Created .env file from template${NC}"
    echo -e "${YELLOW}  ⚠  NOTE: Edit .env if you plan to use API keys${NC}"
else
    echo -e "${BLUE}  ℹ .env file already exists${NC}"
fi

# Step 6: Initialize database
echo -e "${YELLOW}[6/9] Initializing database...${NC}"
if [ "$USE_POSTGRESQL" = true ]; then
    echo -e "${BLUE}  ℹ PostgreSQL mode - ensure TRADING_MTQ_DATABASE_URL is set in .env${NC}"
else
    echo -e "${BLUE}  ℹ SQLite mode - database will be created automatically${NC}"
fi

if $PYTHON_CMD src/database/migration_utils.py init 2>&1; then
    echo -e "${GREEN}  ✓ Database initialized successfully${NC}"
else
    echo -e "${YELLOW}  ⚠  Database initialization warning (might be already initialized)${NC}"
fi

# Step 7: Run tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${YELLOW}[7/9] Running tests...${NC}"
    if pytest tests/test_models.py tests/test_repositories.py -q > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ All tests passed${NC}"
    else
        echo -e "${YELLOW}  ⚠  Some tests failed (check dependencies)${NC}"
    fi
else
    echo -e "${BLUE}[7/9] Skipping tests (--skip-tests flag)${NC}"
fi

# Step 8: Verify CLI installation
echo -e "${YELLOW}[8/9] Verifying CLI installation...${NC}"
if tradingmtq version > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ CLI commands available${NC}"
else
    echo -e "${RED}  ✗ CLI installation failed${NC}"
    exit 1
fi

# Step 9: Display next steps
echo -e "${YELLOW}[9/9] Setup complete!${NC}"
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Next Steps${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${NC}Since MetaTrader5 is Windows-only, you can:${NC}"
echo ""
echo -e "${GREEN}1. Test the database layer:${NC}"
echo -e "   pytest tests/test_models.py tests/test_repositories.py -v"
echo ""
echo -e "${GREEN}2. Run all available tests:${NC}"
echo -e "   pytest tests/ -v --cov=src.database"
echo ""
echo -e "${GREEN}3. Test database operations:${NC}"
echo -e "   python -c \"from src.database.connection import check_database_health; print('DB:', check_database_health())\""
echo ""
echo -e "${GREEN}4. Query test data (if any):${NC}"
echo -e "   python -c \"from src.database.repository import TradeRepository; from src.database.connection import get_session; repo = TradeRepository(); s = get_session().__enter__(); print('Trades:', len(repo.get_all_trades(s))); s.close()\""
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  For Production Deployment${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${NC}To run the full trading system:${NC}"
echo ""
echo -e "1. Transfer this project to a Windows machine"
echo -e "2. Install MetaTrader 5"
echo -e "3. Run: ${GREEN}deploy\\windows\\quick-start.bat${NC}"
echo -e "4. Configure .env with MT5 credentials"
echo -e "5. Start trading: ${GREEN}tradingmtq trade --demo${NC}"
echo ""
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${GREEN}✓ Development setup successful!${NC}"
echo ""
echo -e "Activate environment: ${YELLOW}source venv/bin/activate${NC}"
echo ""
