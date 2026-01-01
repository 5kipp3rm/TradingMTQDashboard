# Hybrid Configuration Design: Database + YAML

## Problem Statement

You're absolutely right to question the current design! Having **two separate systems** doesn't make sense:

1. **Database** (`TradingAccount` model): Stores account credentials, metadata
2. **YAML files** (`config/accounts/account-*.yml`): Stores trading configuration

This creates:
- ❌ **Duplication**: Account info exists in both places
- ❌ **Sync issues**: Changes in one place don't reflect in the other
- ❌ **Complexity**: Two sources of truth
- ❌ **Poor UX**: Users must manage both database records AND YAML files

## Current Architecture (Problematic)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT (BROKEN) DESIGN                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  DATABASE (SQLite)                    YAML FILES                 │
│  ┌──────────────────┐                ┌─────────────────────┐    │
│  │ TradingAccount   │                │ account-001.yml     │    │
│  ├──────────────────┤                ├─────────────────────┤    │
│  │ id: 1            │                │ account_id: "..."   │    │
│  │ account_number   │                │ login: 5012345678   │    │
│  │ account_name     │                │ password: "..."     │    │
│  │ broker           │                │ server: "..."       │    │
│  │ server           │                │ platform_type: MT5  │    │
│  │ password         │                │ currencies: [...]   │    │
│  │ is_active        │                │ risk: {...}         │    │
│  │ created_at       │                │ strategy: {...}     │    │
│  └──────────────────┘                └─────────────────────┘    │
│         ↑                                      ↑                 │
│         │                                      │                 │
│         │    DUPLICATION & SYNC PROBLEMS       │                 │
│         └──────────────────────────────────────┘                 │
│                                                                   │
│  UI adds account to DB → Must manually create YAML              │
│  YAML updated → Must manually update DB                          │
│  Two sources of truth = CHAOS                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Proposed Solution: Hybrid Database + YAML Reference

### Design Pattern: **Single Source of Truth with External Configuration**

```
┌───────────────────────────────────────────────────────────────────────┐
│                    PROPOSED (HYBRID) DESIGN                            │
├───────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DATABASE (Primary Source of Truth)                                    │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │ TradingAccount (Enhanced)                                     │      │
│  ├─────────────────────────────────────────────────────────────┤      │
│  │ # Core Identity                                               │      │
│  │ id: int (primary key)                                         │      │
│  │ account_number: int (unique, indexed)                         │      │
│  │ account_name: str                                             │      │
│  │                                                                │      │
│  │ # Platform Credentials                                        │      │
│  │ broker: str                                                    │      │
│  │ server: str                                                    │      │
│  │ password_encrypted: str                                        │      │
│  │ platform_type: enum (MT4/MT5)                                 │      │
│  │                                                                │      │
│  │ # Status & Metadata                                           │      │
│  │ is_active: bool                                                │      │
│  │ is_default: bool                                               │      │
│  │ is_demo: bool                                                  │      │
│  │ created_at, updated_at, last_connected                         │      │
│  │                                                                │      │
│  │ # NEW: Configuration Reference                                │      │
│  │ config_source: enum (database, yaml, hybrid)                  │      │
│  │ config_path: str (nullable) → "config/accounts/acc-001.yml"  │      │
│  │                                                                │      │
│  │ # NEW: JSON Configuration (Optional)                          │      │
│  │ trading_config_json: JSON (nullable)                          │      │
│  │ ├─ risk: {risk_percent, max_positions, ...}                   │      │
│  │ ├─ currencies: [{symbol, enabled, risk, strategy}]            │      │
│  │ └─ settings: {...}                                             │      │
│  │                                                                │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                   │                                     │
│                                   ↓                                     │
│                    Configuration Resolution Layer                      │
│                    ┌──────────────────────────┐                        │
│                    │   ConfigResolver         │                        │
│                    │  1. Check config_source  │                        │
│                    │  2. Load from DB or YAML │                        │
│                    │  3. Merge with defaults  │                        │
│                    │  4. Return final config  │                        │
│                    └──────────────────────────┘                        │
│                                   │                                     │
│                    ┌──────────────┴──────────────┐                     │
│                    ↓                              ↓                     │
│         ┌──────────────────┐          ┌──────────────────┐            │
│         │ Database Config  │          │   YAML Config    │            │
│         │ (trading_config  │          │ (external file)  │            │
│         │  _json column)   │          │ config/accounts/ │            │
│         └──────────────────┘          │ account-001.yml  │            │
│                                        └──────────────────┘            │
│                                                                         │
└───────────────────────────────────────────────────────────────────────┘
```

## Three Configuration Modes

### Mode 1: Database-Only (Simple)
**Best for**: Beginners, single-account users, web UI management

```python
# Account stored in database with embedded config
account = TradingAccount(
    account_number=5012345678,
    account_name="My Trading Account",
    broker="ICMarkets",
    server="ICMarkets-Demo",
    password_encrypted="...",
    config_source=ConfigSource.DATABASE,
    config_path=None,
    trading_config_json={
        "risk": {"risk_percent": 1.0, "max_positions": 5},
        "currencies": [
            {"symbol": "EURUSD", "enabled": True, "risk": {...}},
            {"symbol": "GBPUSD", "enabled": True, "risk": {...}}
        ]
    }
)
```

**Advantages**:
- ✅ All managed through web UI
- ✅ No YAML files needed
- ✅ Easy for non-technical users
- ✅ Single source of truth
- ✅ Version controlled via migrations

**Disadvantages**:
- ❌ Harder to version control config changes
- ❌ No external editor support
- ❌ Can't easily share configs between environments

### Mode 2: YAML-Only (Advanced)
**Best for**: Power users, DevOps, GitOps workflows, multi-environment

```python
# Account credentials in DB, config in YAML
account = TradingAccount(
    account_number=5012345678,
    account_name="My Trading Account",
    broker="ICMarkets",
    server="ICMarkets-Demo",
    password_encrypted="...",
    config_source=ConfigSource.YAML,
    config_path="config/accounts/account-5012345678.yml",
    trading_config_json=None  # Not used
)
```

**YAML File** (`config/accounts/account-5012345678.yml`):
```yaml
account_id: "account-5012345678"
risk:
  risk_percent: 1.0
  max_positions: 5
currencies:
  - symbol: "EURUSD"
    enabled: true
    risk: {risk_percent: 1.0}
```

**Advantages**:
- ✅ Version control friendly (Git)
- ✅ Easy to diff changes
- ✅ Can use external editors (VSCode, etc.)
- ✅ Easy to template and replicate
- ✅ Supports comments and documentation
- ✅ Environment-specific configs (dev/staging/prod)

**Disadvantages**:
- ❌ Requires file system access
- ❌ More complex for non-technical users
- ❌ Need to manage file permissions

### Mode 3: Hybrid (Best of Both Worlds)
**Best for**: Teams, complex setups, gradual migration

```python
# Credentials in DB, config in YAML, with DB overrides
account = TradingAccount(
    account_number=5012345678,
    account_name="My Trading Account",
    broker="ICMarkets",
    server="ICMarkets-Demo",
    password_encrypted="...",
    config_source=ConfigSource.HYBRID,
    config_path="config/accounts/account-5012345678.yml",
    trading_config_json={
        "risk": {"risk_percent": 0.5}  # Override YAML default
    }
)
```

**Resolution Order**:
1. Load YAML base configuration
2. Apply database overrides from `trading_config_json`
3. Merge with global defaults
4. Return final configuration

**Advantages**:
- ✅ Combine benefits of both approaches
- ✅ YAML for base config, DB for quick tweaks
- ✅ Can gradually migrate between modes
- ✅ Flexible for different use cases

## Database Schema Changes

### Enhanced TradingAccount Model

```python
from sqlalchemy import String, Integer, Enum as SQLEnum, JSON
from enum import Enum

class ConfigSource(str, Enum):
    """Configuration source strategy"""
    DATABASE = "database"  # Config stored in trading_config_json
    YAML = "yaml"          # Config loaded from config_path file
    HYBRID = "hybrid"      # YAML base + database overrides

class TradingAccount(Base):
    __tablename__ = 'trading_accounts'

    # ... existing fields ...

    # NEW: Configuration Management
    config_source: Mapped[ConfigSource] = mapped_column(
        SQLEnum(ConfigSource),
        default=ConfigSource.DATABASE,
        nullable=False
    )

    config_path: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Path to YAML config file (if config_source is YAML or HYBRID)"
    )

    trading_config_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON trading configuration (if config_source is DATABASE or HYBRID overrides)"
    )

    # Configuration validation
    config_validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last time configuration was validated"
    )

    config_validation_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last configuration validation error (if any)"
    )
```

### Migration Script

```python
"""
Add configuration management fields to trading_accounts

Revision ID: add_config_management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

def upgrade():
    # Add new columns
    op.add_column('trading_accounts', sa.Column('config_source', sa.String(20), nullable=False, server_default='database'))
    op.add_column('trading_accounts', sa.Column('config_path', sa.String(255), nullable=True))
    op.add_column('trading_accounts', sa.Column('trading_config_json', sa.JSON(), nullable=True))
    op.add_column('trading_accounts', sa.Column('config_validated_at', sa.DateTime(), nullable=True))
    op.add_column('trading_accounts', sa.Column('config_validation_error', sa.Text(), nullable=True))

    # Create index on config_source for fast filtering
    op.create_index('idx_config_source', 'trading_accounts', ['config_source'])

def downgrade():
    op.drop_index('idx_config_source', table_name='trading_accounts')
    op.drop_column('trading_accounts', 'config_validation_error')
    op.drop_column('trading_accounts', 'config_validated_at')
    op.drop_column('trading_accounts', 'trading_config_json')
    op.drop_column('trading_accounts', 'config_path')
    op.drop_column('trading_accounts', 'config_source')
```

## Configuration Resolution Service

```python
from typing import Optional
from pathlib import Path
import yaml

class ConfigurationResolver:
    """
    Resolves trading configuration from multiple sources:
    - Database JSON
    - YAML files
    - Hybrid (YAML + database overrides)
    - Global defaults
    """

    def __init__(self, defaults_path: str = "config/accounts/default.yml"):
        self.defaults_path = Path(defaults_path)
        self.global_defaults = self._load_defaults()

    def resolve_account_config(self, account: TradingAccount) -> AccountConfig:
        """
        Resolve final account configuration based on config_source strategy

        Resolution order:
        1. Global defaults (default.yml)
        2. YAML file (if applicable)
        3. Database JSON (if applicable)
        4. Validation and merging
        """

        if account.config_source == ConfigSource.DATABASE:
            return self._resolve_database_config(account)

        elif account.config_source == ConfigSource.YAML:
            return self._resolve_yaml_config(account)

        elif account.config_source == ConfigSource.HYBRID:
            return self._resolve_hybrid_config(account)

        else:
            raise ValueError(f"Unknown config_source: {account.config_source}")

    def _resolve_database_config(self, account: TradingAccount) -> AccountConfig:
        """Load config entirely from database JSON"""
        if not account.trading_config_json:
            # Use global defaults
            return self._create_default_config(account)

        # Merge database config with defaults
        config_dict = self._merge_configs(
            base=self.global_defaults,
            override=account.trading_config_json
        )

        return self._dict_to_account_config(account, config_dict)

    def _resolve_yaml_config(self, account: TradingAccount) -> AccountConfig:
        """Load config entirely from YAML file"""
        if not account.config_path:
            raise ValueError(f"Account {account.id} has config_source=YAML but no config_path")

        yaml_path = Path(account.config_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML config not found: {yaml_path}")

        with open(yaml_path, 'r') as f:
            yaml_config = yaml.safe_load(f)

        # Merge YAML config with defaults
        config_dict = self._merge_configs(
            base=self.global_defaults,
            override=yaml_config
        )

        return self._dict_to_account_config(account, config_dict)

    def _resolve_hybrid_config(self, account: TradingAccount) -> AccountConfig:
        """Load YAML base, apply database overrides"""
        # Step 1: Load YAML base
        yaml_config = self._load_yaml(account.config_path)

        # Step 2: Merge with global defaults
        config_dict = self._merge_configs(
            base=self.global_defaults,
            override=yaml_config
        )

        # Step 3: Apply database overrides (highest priority)
        if account.trading_config_json:
            config_dict = self._merge_configs(
                base=config_dict,
                override=account.trading_config_json
            )

        return self._dict_to_account_config(account, config_dict)

    def _merge_configs(self, base: dict, override: dict) -> dict:
        """Deep merge two configuration dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def validate_config(self, account: TradingAccount) -> tuple[bool, Optional[str]]:
        """
        Validate account configuration

        Returns:
            (is_valid, error_message)
        """
        try:
            config = self.resolve_account_config(account)
            config.validate()  # Uses Phase 4 validation
            return (True, None)
        except Exception as e:
            return (False, str(e))
```

## API Endpoints for Configuration Management

### 1. Create Account with Configuration

```python
@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreateRequest,
    config_source: ConfigSource = ConfigSource.DATABASE,
    config_data: Optional[dict] = None,
    config_path: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create new trading account with configuration

    Examples:

    # Database-only mode
    POST /api/accounts
    {
        "account_number": 5012345678,
        "account_name": "My Account",
        "broker": "ICMarkets",
        "server": "ICMarkets-Demo",
        "password": "...",
        "config_source": "database",
        "config_data": {
            "risk": {"risk_percent": 1.0},
            "currencies": [...]
        }
    }

    # YAML mode
    POST /api/accounts
    {
        "account_number": 5012345678,
        "account_name": "My Account",
        "broker": "ICMarkets",
        "server": "ICMarkets-Demo",
        "password": "...",
        "config_source": "yaml",
        "config_path": "config/accounts/account-5012345678.yml"
    }
    """
    # Create account
    account = TradingAccount(
        account_number=account_data.account_number,
        account_name=account_data.account_name,
        # ... other fields ...
        config_source=config_source,
        config_path=config_path,
        trading_config_json=config_data
    )

    # Validate configuration
    resolver = ConfigurationResolver()
    is_valid, error = resolver.validate_config(account)

    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {error}")

    account.config_validated_at = datetime.utcnow()

    db.add(account)
    db.commit()

    return account
```

### 2. Update Account Configuration

```python
@router.put("/accounts/{account_id}/config", response_model=AccountResponse)
async def update_account_config(
    account_id: int,
    config_update: ConfigUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update account configuration

    Can switch between config modes or update config data

    Examples:

    # Switch from DATABASE to YAML
    PUT /api/accounts/1/config
    {
        "config_source": "yaml",
        "config_path": "config/accounts/account-5012345678.yml",
        "export_existing_to_yaml": true  # Export current DB config to YAML
    }

    # Update database config
    PUT /api/accounts/1/config
    {
        "config_data": {
            "risk": {"risk_percent": 0.5}  # Partial update
        },
        "merge": true  # Merge with existing, don't replace
    }
    """
    account = db.query(TradingAccount).filter_by(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Handle config source change
    if config_update.config_source:
        account.config_source = config_update.config_source
        account.config_path = config_update.config_path

    # Handle config data update
    if config_update.config_data:
        if config_update.merge and account.trading_config_json:
            # Merge with existing
            resolver = ConfigurationResolver()
            account.trading_config_json = resolver._merge_configs(
                account.trading_config_json,
                config_update.config_data
            )
        else:
            # Replace entirely
            account.trading_config_json = config_update.config_data

    # Validate
    resolver = ConfigurationResolver()
    is_valid, error = resolver.validate_config(account)

    if not is_valid:
        account.config_validation_error = error
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {error}")

    account.config_validated_at = datetime.utcnow()
    account.config_validation_error = None
    account.updated_at = datetime.utcnow()

    db.commit()

    return account
```

### 3. Get Resolved Configuration

```python
@router.get("/accounts/{account_id}/config/resolved")
async def get_resolved_config(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the final resolved configuration for an account

    This shows what the trading bot will actually use,
    after merging defaults, YAML, and database overrides
    """
    account = db.query(TradingAccount).filter_by(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    resolver = ConfigurationResolver()
    config = resolver.resolve_account_config(account)

    return {
        "account_id": account.id,
        "account_number": account.account_number,
        "config_source": account.config_source.value,
        "config_path": account.config_path,
        "resolved_config": config.to_dict(),
        "resolution_sources": {
            "global_defaults": True,
            "yaml_file": account.config_source in [ConfigSource.YAML, ConfigSource.HYBRID],
            "database_json": account.config_source in [ConfigSource.DATABASE, ConfigSource.HYBRID],
        }
    }
```

### 4. Export Database Config to YAML

```python
@router.post("/accounts/{account_id}/config/export-yaml")
async def export_config_to_yaml(
    account_id: int,
    output_path: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export current database configuration to YAML file

    Useful for:
    - Migrating from DATABASE to YAML mode
    - Creating templates
    - Backing up configurations
    """
    account = db.query(TradingAccount).filter_by(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not output_path:
        output_path = f"config/accounts/account-{account.account_number}.yml"

    # Get resolved config
    resolver = ConfigurationResolver()
    config = resolver.resolve_account_config(account)

    # Write to YAML
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

    return {
        "success": True,
        "output_path": str(output_file),
        "message": f"Configuration exported to {output_file}"
    }
```

## UI Changes Required

### Account Form (Add/Edit)

Add configuration mode selector:

```html
<div class="form-group">
    <label>Configuration Mode</label>
    <select id="configSource" name="config_source">
        <option value="database" selected>Database (Simple - All in UI)</option>
        <option value="yaml">YAML File (Advanced - Version Control)</option>
        <option value="hybrid">Hybrid (YAML + UI Overrides)</option>
    </select>
    <small class="form-help">
        <strong>Database:</strong> Easy, managed entirely through web UI<br>
        <strong>YAML:</strong> Advanced, version control friendly<br>
        <strong>Hybrid:</strong> Best of both worlds
    </small>
</div>

<!-- Show conditionally based on config_source -->
<div id="yamlConfigSection" style="display: none;">
    <div class="form-group">
        <label>YAML Config Path</label>
        <input type="text" id="configPath" name="config_path"
               placeholder="config/accounts/account-5012345678.yml">
        <button type="button" class="btn btn-secondary btn-sm"
                onclick="generateYAMLPath()">
            Auto-generate path
        </button>
    </div>
</div>

<div id="databaseConfigSection">
    <!-- Trading configuration form fields -->
    <h3>Trading Configuration</h3>

    <div class="form-group">
        <label>Risk Per Trade (%)</label>
        <input type="number" step="0.1" name="risk_percent" value="1.0">
    </div>

    <div class="form-group">
        <label>Max Positions Per Pair</label>
        <input type="number" name="max_positions" value="5">
    </div>

    <!-- Currency pairs configuration -->
    <div id="currenciesConfig">
        <!-- Dynamic currency pair configuration -->
    </div>
</div>
```

### Accounts List

Add configuration mode indicator:

```html
<table>
    <thead>
        <tr>
            <th>Account</th>
            <th>Broker</th>
            <th>Config Mode</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>5012345678</td>
            <td>ICMarkets</td>
            <td>
                <span class="badge badge-database">Database</span>
                <!-- or -->
                <span class="badge badge-yaml">YAML</span>
                <!-- or -->
                <span class="badge badge-hybrid">Hybrid</span>
            </td>
            <td>Connected</td>
            <td>
                <button onclick="editConfig(accountId)">Edit Config</button>
                <button onclick="viewResolvedConfig(accountId)">View Resolved</button>
                <button onclick="exportToYAML(accountId)">Export to YAML</button>
            </td>
        </tr>
    </tbody>
</table>
```

## Migration Path for Existing Users

### Phase 1: Add Support (Non-Breaking)
1. Add new database columns with defaults
2. All existing accounts default to `config_source=DATABASE`
3. YAML support added but optional

### Phase 2: Gradual Migration
1. Users can export existing configs to YAML
2. Users can switch individual accounts to YAML mode
3. Both modes work simultaneously

### Phase 3: Cleanup (Optional)
1. Users fully migrated to preferred mode
2. Can deprecate unused mode if desired
3. Or keep both modes available

## Recommended Approach

### For Your Use Case (Multi-Account Trading Bot)

I recommend **Mode 3: Hybrid** as the default:

**Database stores:**
- ✅ Account credentials (login, password, server)
- ✅ Account metadata (name, broker, status)
- ✅ Quick runtime overrides (temporarily disable a pair)

**YAML stores:**
- ✅ Trading strategies and risk settings
- ✅ Currency pair configurations
- ✅ Complex nested settings

**Why Hybrid?**
1. **Security**: Credentials in database (encrypted), not in version control
2. **Flexibility**: Config in YAML (easy to edit, version, template)
3. **Simplicity**: UI can manage both without complexity
4. **Best practices**: Separation of credentials from configuration

### Implementation Priority

```
Priority 1 (Must Have):
├─ Database schema changes (add config fields)
├─ ConfigurationResolver service
├─ Mode 1: Database-only support (existing behavior)
└─ Migration for existing accounts

Priority 2 (High Value):
├─ Mode 2: YAML-only support
├─ Mode 3: Hybrid support
├─ Export to YAML endpoint
└─ UI updates for config mode selection

Priority 3 (Nice to Have):
├─ Config validation UI
├─ Config diff viewer
├─ Template management
└─ Import from YAML

Priority 4 (Future):
├─ Config versioning
├─ Rollback support
├─ A/B testing configs
└─ Config marketplace (share strategies)
```

## Summary

**Current Problem**: Two separate systems (database + YAML) with duplication and sync issues

**Proposed Solution**: Hybrid system where:
- Database is primary source of truth for identity and credentials
- Configuration can live in database, YAML, or both
- ConfigurationResolver merges all sources intelligently
- UI supports all modes seamlessly

**Key Benefits**:
1. ✅ Single source of truth (database account record)
2. ✅ Flexible configuration storage (database, YAML, or hybrid)
3. ✅ No duplication or sync problems
4. ✅ Supports both simple and advanced use cases
5. ✅ Version control friendly (YAML)
6. ✅ UI friendly (database)
7. ✅ Secure (credentials separate from config)
8. ✅ Backward compatible migration path

This design gives you the best of both worlds while eliminating the problems of the current dual-system approach.
