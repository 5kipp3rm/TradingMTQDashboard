# CLI Implementation - WORKING ✅

## Installation

```bash
pip install -e .
```

## Available Commands

### Main Commands

```bash
# Show help
tradingmtq --help
mtq --help              # Shorthand version

# Show version
tradingmtq version

# System check
tradingmtq check

# Start trading (default config)
tradingmtq trade

# Start trading with options
tradingmtq trade --aggressive                    # Use aggressive config
tradingmtq trade -c config/custom.yaml          # Custom config file
tradingmtq trade --demo                         # Demo mode
tradingmtq trade -i 30 -m 20                   # Override interval & max concurrent
tradingmtq trade --aggressive --demo            # Combine options
```

## Command Details

### `tradingmtq trade` Options:
- `-c, --config FILE` - Configuration file path (default: config/currencies.yaml)
- `-a, --aggressive` - Use aggressive trading configuration
- `-d, --demo` - Run in demo/paper trading mode
- `-i, --interval SECONDS` - Override interval from config
- `-m, --max-concurrent INT` - Override max concurrent trades

### `tradingmtq check`
Checks system dependencies and Python version

### `tradingmtq version`  
Shows version and feature list

## Legacy Compatibility

The old way still works:
```bash
python main.py
```

## Implementation Status

✅ Package installed and working
✅ CLI commands functional
✅ Both `tradingmtq` and `mtq` shortcuts work
✅ Help system working
✅ Backward compatible with `python main.py`

## Files Created

```
├── pyproject.toml          - Package configuration with CLI entry points
├── requirements.txt        - Updated with click>=8.1.0
├── main.py                 - Refactored to launch CLI
└── src/cli/
    ├── __init__.py        - CLI module initialization
    ├── app.py             - Main CLI application (Click framework)
    └── commands.py        - Command implementations
```

## Next Steps

1. Add more CLI commands (config, backtest, etc.)
2. Implement full trading logic in commands.py
3. Add configuration management commands
4. Add backtesting commands
5. Git commit the changes
