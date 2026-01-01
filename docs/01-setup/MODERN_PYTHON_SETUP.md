# Modern Python Setup - Quick Guide

**TradingMTQ now uses modern Python packaging standards!**

---

## ✅ New Installation Method

### Quick Start

```bash
# Install with all features
pip install -e ".[all]"
```

### Custom Installation

```bash
# Core only
pip install -e .

# With specific features
pip install -e ".[mt5,ml,llm]"

# Development
pip install -e ".[dev]"
```

---

## 📦 Available Feature Groups

| Group | Install Command | Includes |
|-------|----------------|----------|
| **Core** | `pip install -e .` | FastAPI, SQLAlchemy, scikit-learn, pandas |
| **mt5** | `pip install -e ".[mt5]"` | MetaTrader5 (Windows only) |
| **ml** | `pip install -e ".[ml]"` | TensorFlow, optuna, matplotlib |
| **llm** | `pip install -e ".[llm]"` | OpenAI, Anthropic, BeautifulSoup |
| **postgres** | `pip install -e ".[postgres]"` | PostgreSQL support |
| **dev** | `pip install -e ".[dev]"` | pytest, black, mypy |
| **all** | `pip install -e ".[all]"` | Everything! |

---

## 🎯 Common Scenarios

### Development on macOS/Linux
```bash
pip install -e ".[ml,llm,dev]"
```

### Windows Production Trading
```bash
pip install -e ".[all]"
```

### API Server Only
```bash
pip install -e .
```

### CI/CD Testing
```bash
pip install -e ".[dev]"
```

---

## 🔄 Migrating from requirements.txt

### Old Way ❌
```bash
pip install -r requirements.txt
```

### New Way ✅
```bash
pip install -e ".[all]"
```

**See [PYPROJECT_MIGRATION.md](docs/PYPROJECT_MIGRATION.md) for detailed migration guide.**

---

## 📝 Why This Change?

1. **Standard Approach** - Uses PEP 518/621 (modern Python packaging)
2. **Optional Dependencies** - Install only what you need
3. **Single Source** - No more `requirements.txt` vs `pyproject.toml` sync issues
4. **Better Tooling** - Works with pip, poetry, hatch, etc.
5. **Editable Installs** - Automatic import path setup

---

## ⚡ Quick Commands

```bash
# Fresh install
pip install -e ".[all]"

# Update dependencies
pip install -e ".[all]" --upgrade

# Verify installation
pip show tradingmtq

# List installed packages
pip list

# Test imports
python -c "import src; print('✅ Success!')"
```

---

## 📚 Documentation

- **Migration Guide**: [docs/PYPROJECT_MIGRATION.md](docs/PYPROJECT_MIGRATION.md)
- **Setup Guide**: [docs/01-setup/COMPLETE_SETUP_AND_RUN_GUIDE.md](docs/01-setup/COMPLETE_SETUP_AND_RUN_GUIDE.md)
- **Main README**: [README.md](README.md)

---

**Status**: ✅ Active (as of January 1, 2026)
**Old Method**: Archived (see `docs/99-archive/requirements.txt.old`)
