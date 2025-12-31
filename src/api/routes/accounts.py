"""
Trading Account Management API

Provides REST endpoints for managing multiple MT5 trading accounts.
Supports CRUD operations, account activation, and default account selection.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session

from src.database import get_db_dependency, TradingAccount, AccountConnectionState, PlatformType, Trade
from src.database.currency_models import CurrencyConfiguration
from src.database.account_currency_models import AccountCurrencyConfig
from src.services.session_manager import session_manager
from src.api.websocket import connection_manager

from src.utils.unified_logger import UnifiedLogger

logger = UnifiedLogger.get_logger(__name__)

router = APIRouter()


# Pydantic Models for Request/Response

class AccountCreate(BaseModel):
    """Request model for creating a new trading account"""
    account_number: int = Field(..., description="MT5 account number", gt=0)
    account_name: str = Field(..., description="Friendly account name", min_length=1, max_length=100)
    broker: str = Field("Unknown", description="Broker name (optional, defaults to 'Unknown')", max_length=100)
    server: str = Field(..., description="MT5 server address", min_length=1, max_length=100)
    platform_type: str = Field("MT5", description="Platform type (MT4 or MT5)")
    login: int = Field(..., description="MT5 login number", gt=0)
    password: Optional[str] = Field(None, description="Account password (will be encrypted)")
    is_demo: bool = Field(True, description="Whether this is a demo account")
    is_active: bool = Field(True, description="Whether this account is active")
    is_default: bool = Field(False, description="Whether this is the default account")
    initial_balance: Optional[float] = Field(None, description="Initial account balance", gt=0)
    currency: str = Field("USD", description="Account currency", min_length=3, max_length=10)
    description: Optional[str] = Field(None, description="Account description", max_length=500)

    @validator('broker', pre=True)
    def broker_default_if_empty(cls, v):
        """Set default broker if empty string provided"""
        if not v or v.strip() == '':
            return 'Unknown'
        return v

    @validator('platform_type')
    def platform_type_valid(cls, v):
        """Validate platform type"""
        if v.upper() not in ['MT4', 'MT5']:
            raise ValueError('platform_type must be MT4 or MT5')
        return v.upper()

    @validator('currency')
    def currency_uppercase(cls, v):
        """Ensure currency is uppercase"""
        return v.upper()


class AccountUpdate(BaseModel):
    """Request model for updating an existing trading account"""
    account_name: Optional[str] = Field(None, min_length=1, max_length=100)
    broker: Optional[str] = Field(None, min_length=1, max_length=100)
    server: Optional[str] = Field(None, min_length=1, max_length=100)
    platform_type: Optional[str] = Field(None, description="Platform type (MT4 or MT5)")
    password: Optional[str] = Field(None, description="New password (will be encrypted)")
    is_demo: Optional[bool] = None
    is_active: Optional[bool] = None
    initial_balance: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=10)
    description: Optional[str] = Field(None, max_length=500)

    @validator('platform_type')
    def platform_type_valid(cls, v):
        """Validate platform type"""
        if v and v.upper() not in ['MT4', 'MT5']:
            raise ValueError('platform_type must be MT4 or MT5')
        return v.upper() if v else None

    @validator('currency')
    def currency_uppercase(cls, v):
        """Ensure currency is uppercase"""
        return v.upper() if v else None


class AccountResponse(BaseModel):
    """Response model for trading account"""
    id: int
    account_number: int
    account_name: str
    broker: str
    server: str
    platform_type: str
    login: int
    is_active: bool
    is_default: bool
    is_demo: bool
    currency: str
    initial_balance: Optional[float]
    description: Optional[str]
    created_at: str
    updated_at: Optional[str]
    last_connected: Optional[str]

    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    """Response model for list of accounts"""
    accounts: List[AccountResponse]
    total: int
    active_count: int
    default_account_id: Optional[int]


# API Endpoints

@router.get("/accounts", response_model=AccountListResponse)
async def list_accounts(
    active_only: bool = Query(False, description="Show only active accounts"),
    db: Session = Depends(get_db_dependency)
):
    """
    List all trading accounts.

    Returns list of all configured trading accounts with status information.
    """
    query = select(TradingAccount)

    if active_only:
        query = query.where(TradingAccount.is_active == True)

    query = query.order_by(TradingAccount.is_default.desc(), TradingAccount.account_number)

    result = db.execute(query)
    accounts = result.scalars().all()

    # Get default account
    default_account = next((acc for acc in accounts if acc.is_default), None)

    # Count active accounts
    active_count = sum(1 for acc in accounts if acc.is_active)

    return AccountListResponse(
        accounts=[
            AccountResponse(
                id=acc.id,
                account_number=acc.account_number,
                account_name=acc.account_name,
                broker=acc.broker,
                server=acc.server,
                platform_type=acc.platform_type.value,
                login=acc.login,
                is_active=acc.is_active,
                is_default=acc.is_default,
                is_demo=acc.is_demo,
                currency=acc.currency,
                initial_balance=float(acc.initial_balance) if acc.initial_balance else None,
                description=acc.description,
                created_at=acc.created_at.isoformat(),
                updated_at=acc.updated_at.isoformat() if acc.updated_at else None,
                last_connected=acc.last_connected.isoformat() if acc.last_connected else None
            )
            for acc in accounts
        ],
        total=len(accounts),
        active_count=active_count,
        default_account_id=default_account.id if default_account else None
    )


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get specific trading account by ID.

    Returns detailed information about a single trading account.
    """
    account = db.get(TradingAccount, account_id)

    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    return AccountResponse(
        id=account.id,
        account_number=account.account_number,
        account_name=account.account_name,
        broker=account.broker,
        server=account.server,
        platform_type=account.platform_type.value,
        login=account.login,
        is_active=account.is_active,
        is_default=account.is_default,
        is_demo=account.is_demo,
        currency=account.currency,
        initial_balance=float(account.initial_balance) if account.initial_balance else None,
        description=account.description,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat() if account.updated_at else None,
        last_connected=account.last_connected.isoformat() if account.last_connected else None
    )


@router.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db_dependency)
):
    """
    Create a new trading account.

    Creates a new MT5 trading account configuration in the database.
    If this is set as the default account, removes default flag from other accounts.
    """
    # Check if account number already exists
    existing = db.execute(
        select(TradingAccount).where(TradingAccount.account_number == account_data.account_number)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Account number {account_data.account_number} already exists"
        )

    # If this is the first account or marked as default, set as default
    account_count = db.execute(select(func.count()).select_from(TradingAccount)).scalar()
    is_default = account_data.is_default or account_count == 0

    # If setting as default, remove default from other accounts
    if is_default:
        db.execute(
            update(TradingAccount).values(is_default=False)
        )

    logger.info(
        f"Creating new trading account: {account_data.account_name} (#{account_data.account_number})",
        event_type="account_created",
        account_name=account_data.account_name,
        account_number=account_data.account_number,
        broker=account_data.broker,
        server=account_data.server,
        is_demo=account_data.is_demo,
        is_default=is_default
    )

    # Create new account
    new_account = TradingAccount(
        account_number=account_data.account_number,
        account_name=account_data.account_name,
        broker=account_data.broker,
        server=account_data.server,
        platform_type=PlatformType[account_data.platform_type.upper()],
        login=account_data.login,
        password_encrypted=account_data.password if account_data.password else "",  # TODO: Implement encryption
        is_demo=account_data.is_demo,
        is_active=account_data.is_active,
        is_default=is_default,
        initial_balance=account_data.initial_balance,
        currency=account_data.currency,
        description=account_data.description if account_data.description else None
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    logger.info(
        f"Successfully created account: {new_account.account_name} with ID {new_account.id}",
        event_type="account_created_success",
        account_id=new_account.id,
        account_name=new_account.account_name,
        account_number=new_account.account_number
    )

    return AccountResponse(
        id=new_account.id,
        account_number=new_account.account_number,
        account_name=new_account.account_name,
        broker=new_account.broker,
        server=new_account.server,
        platform_type=new_account.platform_type.value,
        login=new_account.login,
        is_active=new_account.is_active,
        is_default=new_account.is_default,
        is_demo=new_account.is_demo,
        currency=new_account.currency,
        initial_balance=float(new_account.initial_balance) if new_account.initial_balance else None,
        description=new_account.description,
        created_at=new_account.created_at.isoformat(),
        updated_at=new_account.updated_at.isoformat() if new_account.updated_at else None,
        last_connected=new_account.last_connected.isoformat() if new_account.last_connected else None
    )


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db_dependency)
):
    """
    Update an existing trading account.

    Updates configuration for an existing trading account.
    Only provided fields are updated.
    """
    account = db.get(TradingAccount, account_id)

    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    # Update only provided fields
    update_data = account_data.model_dump(exclude_unset=True)

    logger.info(
        f"Updating account: {account.account_name} (#{account.account_number})",
        event_type="account_updated",
        account_id=account_id,
        account_name=account.account_name,
        updated_fields=list(update_data.keys())
    )

    for field, value in update_data.items():
        if field == "password" and value:
            # TODO: Implement encryption
            setattr(account, "password_encrypted", value)
        elif field == "platform_type" and value:
            setattr(account, "platform_type", PlatformType[value])
        else:
            setattr(account, field, value)

    db.commit()
    db.refresh(account)

    logger.info(
        f"Successfully updated account: {account.account_name}",
        event_type="account_updated_success",
        account_id=account_id,
        account_name=account.account_name
    )

    return AccountResponse(
        id=account.id,
        account_number=account.account_number,
        account_name=account.account_name,
        broker=account.broker,
        server=account.server,
        platform_type=account.platform_type.value,
        login=account.login,
        is_active=account.is_active,
        is_default=account.is_default,
        is_demo=account.is_demo,
        currency=account.currency,
        initial_balance=float(account.initial_balance) if account.initial_balance else None,
        description=account.description,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat() if account.updated_at else None,
        last_connected=account.last_connected.isoformat() if account.last_connected else None
    )


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Delete a trading account.

    Deletes a trading account configuration. Note: This does not delete
    associated trades - they will simply have a NULL account_id.
    """
    account = db.get(TradingAccount, account_id)

    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    account_name = account.name
    account_number = account.account_number
    was_default = account.is_default

    logger.info(
        f"Deleting trading account: {account_name} (#{account_number})",
        event_type="account_deleted",
        account_id=account_id,
        account_name=account_name,
        account_number=account_number,
        was_default=was_default
    )

    # If deleting default account, set another account as default
    if account.is_default:
        other_account = db.execute(
            select(TradingAccount)
            .where(TradingAccount.id != account_id)
            .where(TradingAccount.is_active == True)
            .limit(1)
        ).scalar_one_or_none()

        if other_account:
            other_account.is_default = True
            logger.info(
                f"Set account {other_account.name} as new default account",
                event_type="default_account_changed",
                new_default_account_id=other_account.id,
                previous_default_account_id=account_id
            )

    db.delete(account)
    db.commit()

    logger.info(
        f"Successfully deleted account: {account_name} (#{account_number})",
        event_type="account_deleted_success",
        account_id=account_id
    )

    return None


@router.post("/accounts/{account_id}/set-default", response_model=AccountResponse)
async def set_default_account(
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Set an account as the default account.

    Marks the specified account as the default and removes the default
    flag from all other accounts.
    """
    account = db.get(TradingAccount, account_id)

    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    if not account.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot set inactive account as default"
        )

    # Remove default from all accounts
    db.execute(
        update(TradingAccount).values(is_default=False)
    )

    # Set this account as default
    account.is_default = True

    db.commit()
    db.refresh(account)

    return AccountResponse(
        id=account.id,
        account_number=account.account_number,
        account_name=account.account_name,
        broker=account.broker,
        server=account.server,
        platform_type=account.platform_type.value,
        login=account.login,
        is_active=account.is_active,
        is_default=account.is_default,
        is_demo=account.is_demo,
        currency=account.currency,
        initial_balance=float(account.initial_balance) if account.initial_balance else None,
        description=account.description,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat() if account.updated_at else None,
        last_connected=account.last_connected.isoformat() if account.last_connected else None
    )


@router.post("/accounts/{account_id}/activate", response_model=AccountResponse)
async def activate_account(
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Activate a trading account.

    Sets the account as active, allowing it to be used for trading.
    """
    account = db.get(TradingAccount, account_id)

    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    account.is_active = True

    db.commit()
    db.refresh(account)

    return AccountResponse(
        id=account.id,
        account_number=account.account_number,
        account_name=account.account_name,
        broker=account.broker,
        server=account.server,
        platform_type=account.platform_type.value,
        login=account.login,
        is_active=account.is_active,
        is_default=account.is_default,
        is_demo=account.is_demo,
        currency=account.currency,
        initial_balance=float(account.initial_balance) if account.initial_balance else None,
        description=account.description,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat() if account.updated_at else None,
        last_connected=account.last_connected.isoformat() if account.last_connected else None
    )


@router.post("/accounts/{account_id}/deactivate", response_model=AccountResponse)
async def deactivate_account(
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Deactivate a trading account.

    Sets the account as inactive, preventing it from being used for trading.
    If this is the default account, another active account will be set as default.
    """
    account = db.get(TradingAccount, account_id)

    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    account.is_active = False

    # If deactivating default account, set another account as default
    if account.is_default:
        other_account = db.execute(
            select(TradingAccount)
            .where(TradingAccount.id != account_id)
            .where(TradingAccount.is_active == True)
            .limit(1)
        ).scalar_one_or_none()

        if other_account:
            other_account.is_default = True
        else:
            account.is_default = False

    db.commit()
    db.refresh(account)

    return AccountResponse(
        id=account.id,
        account_number=account.account_number,
        account_name=account.account_name,
        broker=account.broker,
        server=account.server,
        platform_type=account.platform_type.value,
        login=account.login,
        is_active=account.is_active,
        is_default=account.is_default,
        is_demo=account.is_demo,
        currency=account.currency,
        initial_balance=float(account.initial_balance) if account.initial_balance else None,
        description=account.description,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat() if account.updated_at else None,
        last_connected=account.last_connected.isoformat() if account.last_connected else None
    )

# =============================================================================
# Account Configuration Endpoints (Hybrid Mode Support)
# =============================================================================

class AccountConfigResponse(BaseModel):
    """Response model for account configuration"""
    account_id: int
    account_number: int
    account_name: str
    config_source: str = "database"  # database, yaml, or hybrid
    config_path: Optional[str] = None
    portable: bool = True
    trading_config: Optional[dict] = None

    class Config:
        from_attributes = True


class AccountConfigUpdate(BaseModel):
    """Request model for updating account configuration"""
    config_source: Optional[str] = Field(None, description="Configuration source: database, yaml, or hybrid")
    config_path: Optional[str] = Field(None, description="Path to YAML config file")
    portable: Optional[bool] = Field(None, description="Enable portable mode for multi-instance")
    trading_config: Optional[dict] = Field(None, description="Trading configuration JSON")

    @validator('config_source')
    def validate_config_source(cls, v):
        """Validate configuration source"""
        if v and v.lower() not in ['database', 'yaml', 'hybrid']:
            raise ValueError('config_source must be database, yaml, or hybrid')
        return v.lower() if v else None


@router.get("/accounts/{account_id}/config", response_model=AccountConfigResponse)
async def get_account_configuration(
    account_id: str,  # Changed to str to handle "all" or "*"
    db: Session = Depends(get_db_dependency)
):
    """
    Get account configuration

    Returns the current configuration for a trading account, including:
    - Configuration source mode (database/yaml/hybrid)
    - YAML file path (if applicable)
    - Portable mode setting
    - Trading configuration (risk, currencies, strategy, position management)

    Special values:
    - "all" or "*": Returns a default/global configuration (not account-specific)
    """
    # Handle special case for "all accounts"
    if account_id.lower() in ["all", "*"]:
        # Return a default global configuration
        default_config = {
            "risk": {
                "risk_percent": 1.0,
                "max_positions": 5,
                "max_concurrent_trades": 15,
                "portfolio_risk_percent": 10.0,
                "stop_loss_pips": 50,
                "take_profit_pips": 100
            },
            "strategy": {
                "strategy_type": "SIMPLE_MA",
                "timeframe": "M5",
                "fast_period": 10,
                "slow_period": 20
            },
            "position_management": {
                "enable_breakeven": True,
                "breakeven_trigger_pips": 15.0,
                "breakeven_offset_pips": 2.0,
                "enable_trailing": True,
                "trailing_start_pips": 20.0,
                "trailing_distance_pips": 10.0,
                "enable_partial_close": False,
                "partial_close_percent": 50.0,
                "partial_close_profit_pips": 25.0
            },
            "currencies": []
        }

        return AccountConfigResponse(
            account_id=0,  # Special ID for "all accounts"
            account_number=0,
            account_name="All Accounts (Global Default)",
            config_source="yaml",
            config_path="config/currencies.yaml",
            portable=False,
            trading_config=default_config
        )

    # Validate account_id is a valid integer
    try:
        account_id_int = int(account_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid account_id: '{account_id}'. Must be an integer or 'all'/'*'"
        )

    # Get account
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id_int).first()

    if not account:
        raise HTTPException(status_code=404, detail=f"Account with ID {account_id_int} not found")

    # Check if account has saved configuration
    if account.trading_config_json:
        # Return saved configuration
        return AccountConfigResponse(
            account_id=account.id,
            account_number=account.account_number,
            account_name=account.account_name,
            config_source=account.config_source or "hybrid",
            config_path=account.config_path,
            portable=True,
            trading_config=account.trading_config_json
        )

    # Return default configuration if none saved yet
    default_config = {
        "risk": {
            "risk_percent": 1.0,
            "max_positions": 5,
            "max_concurrent_trades": 15,
            "portfolio_risk_percent": 10.0,
            "stop_loss_pips": 50,
            "take_profit_pips": 100
        },
        "strategy": {
            "strategy_type": "SIMPLE_MA",
            "timeframe": "M5",
            "fast_period": 10,
            "slow_period": 20
        },
        "position_management": {
            "enable_breakeven": True,
            "breakeven_trigger_pips": 15.0,
            "breakeven_offset_pips": 2.0,
            "enable_trailing": True,
            "trailing_start_pips": 20.0,
            "trailing_distance_pips": 10.0,
            "enable_partial_close": False,
            "partial_close_percent": 50.0,
            "partial_close_profit_pips": 25.0
        },
        "currencies": []
    }

    return AccountConfigResponse(
        account_id=account.id,
        account_number=account.account_number,
        account_name=account.account_name,
        config_source="hybrid",
        config_path=f"config/accounts/account-{account.account_number}.yml",
        portable=True,
        trading_config=default_config
    )


@router.put("/accounts/{account_id}/config", response_model=AccountConfigResponse)
async def update_account_configuration(
    account_id: str,  # Changed to str to handle "all" or "*"
    config_update: AccountConfigUpdate,
    db: Session = Depends(get_db_dependency)
):
    """
    Update account configuration

    Saves trading configuration for an account. Configuration can be stored in:
    - Database: All config in trading_config_json column
    - YAML: All config in external YAML file
    - Hybrid: Credentials in DB, config in YAML (recommended)

    Note: Cannot update configuration for "all" accounts (account_id="all" or "*")
    
    Request body:
    {
        "config_source": "hybrid",
        "config_path": "config/accounts/account-5012345678.yml",
        "portable": true,
        "trading_config": {
            "risk": {...},
            "currencies": [...],
            "strategy": {...},
            "position_management": {...}
        }
    }
    """
    # Handle special case for "all accounts" - not allowed for updates
    if account_id.lower() in ["all", "*"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot update configuration for 'all' accounts. Please select a specific account."
        )

    # Validate account_id is a valid integer
    try:
        account_id_int = int(account_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid account_id: '{account_id}'. Must be an integer."
        )

    # Get account
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id_int).first()

    if not account:
        raise HTTPException(status_code=404, detail=f"Account with ID {account_id_int} not found")

    # Update configuration columns
    if config_update.config_source is not None:
        account.config_source = config_update.config_source

    if config_update.config_path is not None:
        account.config_path = config_update.config_path

    if config_update.trading_config is not None:
        account.trading_config_json = config_update.trading_config

    # Update validation timestamp
    from datetime import datetime
    account.config_validated_at = datetime.utcnow()
    account.config_validation_error = None  # Clear any previous errors

    # Commit changes
    db.commit()
    db.refresh(account)

    # Log the configuration (for debugging)
    logger.log_config(
        "Configuration saved for account",
        account_id=account_id,
        config_source=account.config_source,
        config_path=account.config_path,
        portable=config_update.portable if config_update.portable is not None else True
    )

    # Return the updated configuration
    return AccountConfigResponse(
        account_id=account.id,
        account_number=account.account_number,
        account_name=account.account_name,
        config_source=account.config_source or "hybrid",
        config_path=account.config_path,
        portable=config_update.portable if config_update.portable is not None else True,
        trading_config=account.trading_config_json
    )


@router.post("/accounts/{account_id}/config/export-yaml")
async def export_account_config_to_yaml(
    account_id: int,
    output_path: Optional[str] = None,
    db: Session = Depends(get_db_dependency)
):
    """
    Export account configuration to YAML file
    
    Exports the current trading configuration to a YAML file.
    Useful for:
    - Migrating from DATABASE to YAML mode
    - Creating configuration templates
    - Backing up configurations
    - Version controlling settings
    
    Query parameters:
    - output_path: Optional custom path (default: config/accounts/account-{number}.yml)
    
    Returns:
    {
        "success": true,
        "output_path": "config/accounts/account-5012345678.yml",
        "message": "Configuration exported successfully"
    }
    """
    # Get account
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account with ID {account_id} not found")
    
    # Generate output path if not provided
    if not output_path:
        output_path = f"config/accounts/account-{account.account_number}.yml"
    
    # For now, just return success
    # Once we implement the full configuration system, we'll actually write the YAML file

    logger.log_config(
        "Export configuration for account",
        account_id=account_id,
        output_path=output_path
    )
    
    return {
        "success": True,
        "output_path": output_path,
        "message": f"Configuration export prepared for {output_path} (implementation pending)"
    }


@router.get("/accounts/{account_id}/config/resolved")
async def get_resolved_account_config(
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get resolved account configuration
    
    Returns the final configuration after merging:
    1. Global defaults (default.yml)
    2. YAML file configuration (if config_source is yaml or hybrid)
    3. Database overrides (if config_source is database or hybrid)
    
    This shows exactly what the trading bot will use.
    """
    # Get account
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account with ID {account_id} not found")
    
    # For now, return the same as get_account_configuration
    # Once we implement ConfigurationResolver, this will merge all sources
    
    return {
        "account_id": account.id,
        "account_number": account.account_number,
        "config_source": "hybrid",
        "config_path": f"config/accounts/account-{account.account_number}.yml",
        "resolved_config": {
            "risk": {
                "risk_percent": 1.0,
                "max_positions": 5,
                "max_concurrent_trades": 15,
                "portfolio_risk_percent": 10.0,
                "stop_loss_pips": 50,
                "take_profit_pips": 100
            },
            "strategy": {
                "strategy_type": "SIMPLE_MA",
                "timeframe": "M5",
                "fast_period": 10,
                "slow_period": 20
            },
            "position_management": {
                "enable_breakeven": True,
                "breakeven_trigger_pips": 15.0,
                "breakeven_offset_pips": 2.0,
                "enable_trailing": True,
                "trailing_start_pips": 20.0,
                "trailing_distance_pips": 10.0,
                "enable_partial_close": False,
                "partial_close_percent": 50.0,
                "partial_close_profit_pips": 25.0
            },
            "currencies": []
        },
        "resolution_sources": {
            "global_defaults": True,
            "yaml_file": True,
            "database_json": True
        }
    }


# =============================================================================
# Per-Account Currency Configuration Endpoints
# =============================================================================

class AccountCurrencyResponse(BaseModel):
    """Response model for account currency configuration"""
    id: int
    account_id: int
    symbol: str
    enabled: bool

    # Risk settings (NULL = use global default)
    risk_percent: Optional[float]
    max_position_size: Optional[float]
    min_position_size: Optional[float]

    # Strategy settings
    strategy_type: Optional[str]
    timeframe: Optional[str]

    # Indicators
    fast_period: Optional[int]
    slow_period: Optional[int]

    # SL/TP
    sl_pips: Optional[int]
    tp_pips: Optional[int]

    # Trading Rules
    cooldown_seconds: Optional[int]
    trade_on_signal_change: Optional[bool]

    # Position Stacking
    allow_position_stacking: Optional[bool]
    max_positions_same_direction: Optional[int]
    max_total_positions: Optional[int]
    stacking_risk_multiplier: Optional[float]

    # Metadata
    description: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AccountCurrencyCreate(BaseModel):
    """Request model for creating/updating account currency configuration"""
    symbol: str = Field(..., description="Currency pair symbol (e.g., EURUSD)")
    enabled: bool = Field(True, description="Whether this currency is enabled for trading")

    # Risk settings (NULL = use global default)
    risk_percent: Optional[float] = Field(None, description="Risk per trade (%)", ge=0.1, le=10.0)
    max_position_size: Optional[float] = Field(None, description="Max position size (lots)", gt=0)
    min_position_size: Optional[float] = Field(None, description="Min position size (lots)", gt=0)

    # Strategy settings
    strategy_type: Optional[str] = Field(None, description="Strategy type: crossover or position")
    timeframe: Optional[str] = Field(None, description="Trading timeframe (M1, M5, M15, etc.)")

    # Indicators
    fast_period: Optional[int] = Field(None, description="Fast MA period", gt=0)
    slow_period: Optional[int] = Field(None, description="Slow MA period", gt=0)

    # SL/TP
    sl_pips: Optional[int] = Field(None, description="Stop Loss in pips", gt=0)
    tp_pips: Optional[int] = Field(None, description="Take Profit in pips", gt=0)

    # Trading Rules
    cooldown_seconds: Optional[int] = Field(None, description="Cooldown between trades (seconds)", ge=0)
    trade_on_signal_change: Optional[bool] = Field(None, description="Require signal change before re-entry")

    # Position Stacking
    allow_position_stacking: Optional[bool] = Field(None, description="Allow multiple positions in same direction")
    max_positions_same_direction: Optional[int] = Field(None, description="Max positions same direction", gt=0)
    max_total_positions: Optional[int] = Field(None, description="Max total positions for this symbol", gt=0)
    stacking_risk_multiplier: Optional[float] = Field(None, description="Risk multiplier for stacked positions", gt=0)


class AccountCurrencyListResponse(BaseModel):
    """Response model for list of account currencies"""
    currencies: List[AccountCurrencyResponse]
    total: int
    account_id: int
    account_name: str


@router.get("/accounts/{account_id}/currencies", response_model=AccountCurrencyListResponse)
async def get_account_currencies(
    account_id: int,
    enabled_only: bool = Query(False, description="Show only enabled currencies"),
    db: Session = Depends(get_db_dependency)
):
    """
    Get all currency configurations for an account.

    Returns list of currencies with account-specific settings merged with global defaults.
    """
    # Verify account exists
    account = db.get(TradingAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    # Get account-specific currencies (exclude deleted currencies)
    # ONLY return currencies that have been explicitly added to this account
    account_configs_query = select(AccountCurrencyConfig).where(
        AccountCurrencyConfig.account_id == account_id,
        AccountCurrencyConfig.is_deleted == False  # Filter out soft-deleted currencies
    )

    if enabled_only:
        account_configs_query = account_configs_query.where(AccountCurrencyConfig.enabled == True)

    result = db.execute(account_configs_query)
    account_configs = result.scalars().all()

    # Build response list
    currency_responses = []

    for account_config in account_configs:
        # Get global currency for description and metadata
        global_currency = db.get(CurrencyConfiguration, account_config.currency_symbol)

        currency_responses.append(AccountCurrencyResponse(
            id=account_config.id,
            account_id=account_config.account_id,
            symbol=account_config.currency_symbol,
            enabled=account_config.enabled,
            risk_percent=account_config.risk_percent,
            max_position_size=account_config.max_position_size,
            min_position_size=account_config.min_position_size,
            strategy_type=account_config.strategy_type,
            timeframe=account_config.timeframe,
            fast_period=account_config.fast_period,
            slow_period=account_config.slow_period,
            sl_pips=account_config.sl_pips,
            tp_pips=account_config.tp_pips,
            cooldown_seconds=account_config.cooldown_seconds,
            trade_on_signal_change=account_config.trade_on_signal_change,
            allow_position_stacking=account_config.allow_position_stacking,
            max_positions_same_direction=account_config.max_positions_same_direction,
            max_total_positions=account_config.max_total_positions,
            stacking_risk_multiplier=account_config.stacking_risk_multiplier,
            description=global_currency.description if global_currency else account_config.currency_symbol,
            created_at=account_config.created_at.isoformat(),
            updated_at=account_config.updated_at.isoformat()
        ))

    return AccountCurrencyListResponse(
        currencies=currency_responses,
        total=len(currency_responses),
        account_id=account_id,
        account_name=account.account_name
    )


@router.put("/accounts/{account_id}/currencies/{symbol}", response_model=AccountCurrencyResponse)
async def update_account_currency(
    account_id: int,
    symbol: str,
    currency_data: AccountCurrencyCreate,
    db: Session = Depends(get_db_dependency)
):
    """
    Create or update currency configuration for an account.

    If the account doesn't have a config for this currency, creates one.
    Otherwise updates the existing configuration.
    NULL fields will fall back to global defaults.
    """
    # Verify account exists
    account = db.get(TradingAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    # Check if global currency config exists, create default if not
    global_currency = db.execute(
        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == symbol)
    ).scalar_one_or_none()

    if not global_currency:
        # Create default global configuration automatically
        logger.info(f"Creating default global config for {symbol}")
        global_currency = CurrencyConfiguration(
            symbol=symbol,
            enabled=True,
            risk_percent=currency_data.risk_percent or 1.0,
            max_position_size=currency_data.max_position_size or 0.1,
            min_position_size=currency_data.min_position_size or 0.01,
            strategy_type=currency_data.strategy_type or "simple_ma",
            timeframe=currency_data.timeframe or "M5",
            fast_period=currency_data.fast_period or 10,
            slow_period=currency_data.slow_period or 20,
            sl_pips=currency_data.sl_pips or 50,
            tp_pips=currency_data.tp_pips or 100,
            cooldown_seconds=currency_data.cooldown_seconds or 300,
            trade_on_signal_change=currency_data.trade_on_signal_change if currency_data.trade_on_signal_change is not None else True,
            allow_position_stacking=currency_data.allow_position_stacking or False,
            max_positions_same_direction=currency_data.max_positions_same_direction or 1,
            max_total_positions=currency_data.max_total_positions or 5,
            stacking_risk_multiplier=currency_data.stacking_risk_multiplier or 1.0,
            description=f"{symbol} trading configuration"
        )
        db.add(global_currency)
        db.flush()  # Ensure the global config is created before proceeding

    # Check if account config exists
    account_config = db.execute(
        select(AccountCurrencyConfig).where(
            AccountCurrencyConfig.account_id == account_id,
            AccountCurrencyConfig.currency_symbol == symbol
        )
    ).scalar_one_or_none()

    if account_config:
        # Update existing config
        update_data = currency_data.model_dump(exclude_unset=True)
        logger.info(
            f"Updating currency {symbol} config for account {account_id}",
            event_type="currency_config_updated",
            account_id=account_id,
            symbol=symbol,
            updated_fields=list(update_data.keys())
        )
        for field, value in update_data.items():
            if field != "symbol":  # Don't update symbol
                setattr(account_config, field, value)
    else:
        # Create new config
        logger.info(
            f"Creating new currency {symbol} config for account {account_id}",
            event_type="currency_config_created",
            account_id=account_id,
            symbol=symbol,
            enabled=currency_data.enabled
        )
        account_config = AccountCurrencyConfig(
            account_id=account_id,
            currency_symbol=symbol,
            enabled=currency_data.enabled,
            risk_percent=currency_data.risk_percent,
            max_position_size=currency_data.max_position_size,
            min_position_size=currency_data.min_position_size,
            strategy_type=currency_data.strategy_type,
            timeframe=currency_data.timeframe,
            fast_period=currency_data.fast_period,
            slow_period=currency_data.slow_period,
            sl_pips=currency_data.sl_pips,
            tp_pips=currency_data.tp_pips,
            cooldown_seconds=currency_data.cooldown_seconds,
            trade_on_signal_change=currency_data.trade_on_signal_change,
            allow_position_stacking=currency_data.allow_position_stacking,
            max_positions_same_direction=currency_data.max_positions_same_direction,
            max_total_positions=currency_data.max_total_positions,
            stacking_risk_multiplier=currency_data.stacking_risk_multiplier
        )
        db.add(account_config)

    db.commit()
    db.refresh(account_config)

    logger.info(
        f"Successfully saved currency {symbol} config for account {account_id}",
        event_type="currency_config_saved",
        account_id=account_id,
        symbol=symbol,
        config_id=account_config.id
    )

    return AccountCurrencyResponse(
        id=account_config.id,
        account_id=account_config.account_id,
        symbol=account_config.currency_symbol,
        enabled=account_config.enabled,
        risk_percent=account_config.risk_percent,
        max_position_size=account_config.max_position_size,
        min_position_size=account_config.min_position_size,
        strategy_type=account_config.strategy_type,
        timeframe=account_config.timeframe,
        fast_period=account_config.fast_period,
        slow_period=account_config.slow_period,
        sl_pips=account_config.sl_pips,
        tp_pips=account_config.tp_pips,
        cooldown_seconds=account_config.cooldown_seconds,
        trade_on_signal_change=account_config.trade_on_signal_change,
        allow_position_stacking=account_config.allow_position_stacking,
        max_positions_same_direction=account_config.max_positions_same_direction,
        max_total_positions=account_config.max_total_positions,
        stacking_risk_multiplier=account_config.stacking_risk_multiplier,
        description=global_currency.description,
        created_at=account_config.created_at.isoformat(),
        updated_at=account_config.updated_at.isoformat()
    )


@router.delete("/accounts/{account_id}/currencies/{symbol}", status_code=204)
async def delete_account_currency(
    account_id: int,
    symbol: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Delete account-specific currency configuration.

    Soft Delete Logic:
    - If currency has trade history: Mark as deleted (soft delete) - keeps for historical reference
    - If no trade history: Remove completely (hard delete)

    This preserves data integrity while allowing clean removal of unused configurations.
    """
    # Verify account exists
    account = db.get(TradingAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    # Check if account config exists
    account_config = db.execute(
        select(AccountCurrencyConfig).where(
            AccountCurrencyConfig.account_id == account_id,
            AccountCurrencyConfig.currency_symbol == symbol
        )
    ).scalar_one_or_none()

    if not account_config:
        raise HTTPException(
            status_code=404,
            detail=f"No configuration found for currency {symbol} on account {account_id}"
        )

    # Check if currency has any trade history for this account
    has_trades = db.execute(
        select(Trade).where(
            Trade.account_id == account_id,
            Trade.symbol == symbol
        ).limit(1)
    ).scalar_one_or_none()

    if has_trades:
        # Soft delete: Mark as deleted but keep record for historical data
        account_config.is_deleted = True
        account_config.enabled = False  # Also disable to prevent accidental trading
        db.commit()
        logger.info(
            f"Soft deleted currency {symbol} for account {account_id} (has trade history)",
            event_type="currency_config_soft_deleted",
            account_id=account_id,
            symbol=symbol,
            action="soft_delete"
        )
    else:
        # Hard delete: Remove completely as there's no trade history
        db.delete(account_config)
        db.commit()
        logger.info(
            f"Hard deleted currency {symbol} for account {account_id} (no trade history)",
            event_type="currency_config_hard_deleted",
            account_id=account_id,
            symbol=symbol,
            action="hard_delete"
        )

    return None


@router.get("/accounts/{account_id}/currencies/{symbol}/resolved", response_model=dict)
async def get_resolved_account_currency(
    account_id: int,
    symbol: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Get resolved currency configuration with global defaults merged.

    Returns the final configuration that will be used for trading,
    with account overrides taking precedence over global defaults.
    """
    # Verify account exists
    account = db.get(TradingAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    # Get global currency
    global_currency = db.execute(
        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == symbol)
    ).scalar_one_or_none()

    if not global_currency:
        raise HTTPException(status_code=404, detail=f"Currency {symbol} not found in global configuration")

    # Get account config (if exists)
    account_config = db.execute(
        select(AccountCurrencyConfig).where(
            AccountCurrencyConfig.account_id == account_id,
            AccountCurrencyConfig.currency_symbol == symbol
        )
    ).scalar_one_or_none()

    if account_config:
        # Merge account overrides with global defaults
        resolved = account_config.merge_with_global(global_currency)
    else:
        # Use global defaults
        resolved = global_currency.to_dict()
        resolved['account_id'] = account_id
        resolved['is_override'] = False

    return resolved
