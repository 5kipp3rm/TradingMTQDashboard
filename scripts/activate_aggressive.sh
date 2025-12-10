#!/bin/bash
# Activate Aggressive Trading Mode
# This script switches to aggressive configuration for maximum profit

echo "=================================================="
echo "  AGGRESSIVE TRADING MODE ACTIVATION"
echo "=================================================="
echo ""

# Backup current config
if [ -f config/currencies.yaml ]; then
    echo "✓ Backing up current configuration..."
    cp config/currencies.yaml config/currencies_backup_$(date +%Y%m%d_%H%M%S).yaml
    echo "  Backup saved to: config/currencies_backup_$(date +%Y%m%d_%H%M%S).yaml"
else
    echo "! No existing currencies.yaml found"
fi

echo ""
echo "✓ Activating aggressive trading configuration..."
cp config/currencies_aggressive.yaml config/currencies.yaml

echo ""
echo "=================================================="
echo "  AGGRESSIVE MODE ACTIVATED"
echo "=================================================="
echo ""
echo "Key Features Enabled:"
echo "  ✓ Position stacking (up to 4 per currency)"
echo "  ✓ Short cooldowns (30-45 seconds)"
echo "  ✓ 6 currency pairs active"
echo "  ✓ 30 max concurrent positions"
echo "  ✓ Lower ML threshold (0.60 = more trades)"
echo ""
echo "Expected Performance:"
echo "  • 30-50 trades per day"
echo "  • +5-15% daily profit potential"
echo "  • +200-1000% monthly target"
echo ""
echo "⚠️  IMPORTANT:"
echo "  • Test on DEMO account first!"
echo "  • Monitor closely for first week"
echo "  • Best for TRENDING markets"
echo "  • Review docs/AGGRESSIVE_TRADING_GUIDE.md"
echo ""
echo "To start trading:"
echo "  python main.py"
echo ""
echo "To revert to conservative mode:"
echo "  cp config/currencies_backup_*.yaml config/currencies.yaml"
echo ""
echo "=================================================="
