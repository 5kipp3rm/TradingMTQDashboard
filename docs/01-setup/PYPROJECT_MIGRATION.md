# Migration to pyproject.toml

**Date**: January 1, 2026
**Change**: Migrated from `requirements.txt` to `pyproject.toml` as single source of truth

---

## What Changed

### Before ❌
```bash
pip install -r requirements.txt  # Old way - requirements.txt
```

### After ✅
```bash
pip install -e .                  # New way - pyproject.toml
```

---

## Why This Change?

### Problems with requirements.txt
1. **Redundant files** - Had both `requirements.txt` and `pyproject.toml`
2. **Manual sync required** - Changes needed in both places
3. **No optional dependencies** - All-or-nothing installation
4. **Not standard** - Modern Python uses `pyproject.toml` (PEP 518, 621)

### Benefits of pyproject.toml
1. **Single source of truth** - All dependencies in one place
2. **Optional features** - Install only what you need
3. **Standard approach** - PEP 518/621 compliant
4. **Better tooling** - Works with pip, poetry, hatch, etc.
5. **Editable installs** - Automatic import path setup

---

## Installation Commands

### Basic Installation (Core Dependencies)

```bash
# Install core dependencies only
pip install -e .
```

**Includes:**
- numpy, pandas (data processing)
- fastapi, uvicorn (web API)
- sqlalchemy, alembic (database)
- scikit-learn (basic ML)
- click (CLI)
- And more core packages

### With Optional Features

```bash
# MT5 Trading (Windows only)
pip install -e ".[mt5]"

# Machine Learning (with TensorFlow)
pip install -e ".[ml]"

# LLM Integration (OpenAI, Anthropic)
pip install -e ".[llm]"

# PostgreSQL Support
pip install -e ".[postgres]"

# Development Tools
pip install -e ".[dev]"

# Multiple features
pip install -e ".[mt5,ml,llm]"

# Everything
pip install -e ".[all]"
```

---

## Installation Scenarios

### Scenario 1: Development (macOS/Linux)

```bash
# Core + ML + LLM + Dev tools (no MT5 on macOS)
pip install -e ".[ml,llm,dev]"
```

### Scenario 2: Windows Production (Full Trading)

```bash
# Everything including MT5
pip install -e ".[all]"
```

### Scenario 3: CI/CD Testing

```bash
# Core + Dev tools only
pip install -e ".[dev]"
```

### Scenario 4: API Server Only

```bash
# Core dependencies only (FastAPI, database)
pip install -e .
```

---

## Dependency Groups

### Core Dependencies (Always Installed)

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | >=1.26.0 | Numerical operations |
| pandas | >=2.2.0 | Data processing |
| fastapi | >=0.104.1 | Web API framework |
| uvicorn | >=0.24.0 | ASGI server |
| sqlalchemy | >=2.0.23 | Database ORM |
| alembic | >=1.13.0 | Database migrations |
| click | >=8.1.0 | CLI framework |
| scikit-learn | >=1.3.0 | Basic ML |
| pydantic | >=2.0.0 | Data validation |
| websockets | >=12.0 | WebSocket support |
| apscheduler | >=3.10.4 | Scheduled jobs |
| reportlab | >=4.0.7 | PDF generation |

### Optional: mt5 (Windows Trading)

| Package | Version | Purpose |
|---------|---------|---------|
| MetaTrader5 | >=5.0.5430 | MT5 API integration |

### Optional: ml (Machine Learning)

| Package | Version | Purpose |
|---------|---------|---------|
| tensorflow | >=2.14.0 | Deep learning (LSTM) |
| optuna | >=3.3.0 | Hyperparameter tuning |
| matplotlib | >=3.7.0 | Plotting |
| seaborn | >=0.12.0 | Statistical visualization |

### Optional: llm (AI Integration)

| Package | Version | Purpose |
|---------|---------|---------|
| openai | >=1.3.0 | GPT-4o API |
| anthropic | >=0.7.0 | Claude API |
| beautifulsoup4 | >=4.12.0 | HTML parsing (news) |

### Optional: postgres (Production Database)

| Package | Version | Purpose |
|---------|---------|---------|
| psycopg2-binary | >=2.9.9 | PostgreSQL adapter |

### Optional: dev (Development Tools)

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=7.4.0 | Testing framework |
| pytest-cov | >=4.1.0 | Code coverage |
| pytest-mock | >=3.11.1 | Mocking support |
| pytest-asyncio | >=0.23.0 | Async testing |
| black | >=23.7.0 | Code formatter |
| flake8 | >=6.1.0 | Linter |
| mypy | >=1.5.1 | Type checker |

---

## Migration Steps

### For Existing Environments

**Step 1: Backup current environment** (optional)
```bash
pip freeze > old_requirements_backup.txt
```

**Step 2: Uninstall old dependencies** (optional - fresh start)
```bash
pip uninstall -y -r requirements.txt
```

**Step 3: Install from pyproject.toml**
```bash
# Choose appropriate features
pip install -e ".[all]"  # Or specific features
```

**Step 4: Verify installation**
```bash
pip list | grep tradingmtq
```

### For New Environments

**Just install directly:**
```bash
pip install -e ".[all]"  # Or specific features
```

---

## Updating Dependencies

### Add New Dependency

**Edit `pyproject.toml`:**
```toml
dependencies = [
    "numpy>=1.26.0",
    "your-new-package>=1.0.0",  # Add here
]
```

**Then reinstall:**
```bash
pip install -e .
```

### Add New Optional Dependency

```toml
[project.optional-dependencies]
mynewfeature = [
    "some-package>=1.0.0",
]
```

**Install with:**
```bash
pip install -e ".[mynewfeature]"
```

---

## CI/CD Updates

### Old CI/CD (requirements.txt)

```yaml
- name: Install dependencies
  run: pip install -r requirements.txt
```

### New CI/CD (pyproject.toml)

```yaml
# Minimal for testing
- name: Install dependencies
  run: pip install -e ".[dev]"

# Or full for comprehensive testing
- name: Install dependencies
  run: pip install -e ".[all]"
```

---

## Troubleshooting

### Issue: Import errors after migration

**Problem**: `ModuleNotFoundError` after switching

**Solution**: Make sure you used `-e` (editable install)
```bash
pip install -e .  # Note the -e flag!
```

### Issue: Missing optional dependencies

**Problem**: Feature doesn't work (e.g., TensorFlow not found)

**Solution**: Install the appropriate optional group
```bash
pip install -e ".[ml]"  # For TensorFlow
```

### Issue: Want to use requirements.txt for now

**Solution**: Generate requirements.txt from pyproject.toml
```bash
pip install pip-tools
pip-compile pyproject.toml -o requirements.txt
```

---

## Documentation Updates

### Setup Guides

All setup documentation has been updated to use `pip install -e ".[...]"` instead of `pip install -r requirements.txt`.

**Updated files:**
- `docs/01-setup/COMPLETE_SETUP_AND_RUN_GUIDE.md`
- `docs/01-setup/SETUP_FROM_SCRATCH.md`
- `docs/01-setup/DEPLOYMENT_GUIDE.md`
- `README.md`

---

## Backward Compatibility

### requirements.txt Status

The old `requirements.txt` file has been **moved to archive** but is kept for reference:
- `docs/99-archive/requirements.txt.old`

If you absolutely need it, you can generate a new one:
```bash
pip freeze > requirements.txt
```

But the recommended approach is to use `pyproject.toml` going forward.

---

## Benefits Summary

| Aspect | requirements.txt | pyproject.toml |
|--------|------------------|----------------|
| **Standard** | ❌ Legacy | ✅ Modern (PEP 518/621) |
| **Optional deps** | ❌ No | ✅ Yes |
| **Editable install** | ❌ Manual PYTHONPATH | ✅ Automatic |
| **Tool support** | ⚠️ Limited | ✅ Universal |
| **Metadata** | ❌ None | ✅ Rich (version, authors, etc.) |
| **CLI scripts** | ❌ Manual | ✅ Automatic entry points |

---

## Quick Reference

**Install core only:**
```bash
pip install -e .
```

**Install with features:**
```bash
pip install -e ".[mt5,ml,llm]"
```

**Install everything:**
```bash
pip install -e ".[all]"
```

**Development setup:**
```bash
pip install -e ".[dev]"
```

**Verify installation:**
```bash
pip show tradingmtq
python -c "import src; print('Success!')"
```

---

## Related Changes

1. **pyproject.toml** - Updated with all dependencies
2. **requirements.txt** - Archived to `docs/99-archive/`
3. **Setup guides** - Updated installation commands
4. **CI/CD examples** - Updated in documentation

---

**Status**: ✅ Migration Complete
**Recommended Action**: Use `pip install -e ".[features]"` going forward
**Backward Compat**: Can still generate requirements.txt if needed
