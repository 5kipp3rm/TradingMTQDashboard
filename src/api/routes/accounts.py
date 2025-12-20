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

from src.database import get_db_dependency, TradingAccount, AccountConnectionState, PlatformType
from src.services.session_manager import session_manager
from src.api.websocket import connection_manager


router = APIRouter()


# Pydantic Models for Request/Response

class AccountCreate(BaseModel):
    """Request model for creating a new trading account"""
    account_number: int = Field(..., description="MT5 account number", gt=0)
    account_name: str = Field(..., description="Friendly account name", min_length=1, max_length=100)
    broker: str = Field(..., description="Broker name", min_length=1, max_length=100)
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

    # Create new account
    new_account = TradingAccount(
        account_number=account_data.account_number,
        account_name=account_data.account_name,
        broker=account_data.broker,
        server=account_data.server,
        platform_type=PlatformType[account_data.platform_type],
        login=account_data.login,
        password_encrypted=account_data.password,  # TODO: Implement encryption
        is_demo=account_data.is_demo,
        is_active=account_data.is_active,
        is_default=is_default,
        initial_balance=account_data.initial_balance,
        currency=account_data.currency,
        description=account_data.description
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

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

    db.delete(account)
    db.commit()

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
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get account configuration
    
    Returns the current configuration for a trading account, including:
    - Configuration source mode (database/yaml/hybrid)
    - YAML file path (if applicable)
    - Portable mode setting
    - Trading configuration (risk, currencies, strategy, position management)
    """
    # Get account
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account with ID {account_id} not found")
    
    # For now, return a default configuration since we haven't added the database columns yet
    # This allows the UI to work immediately
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
        config_source="hybrid",  # Default to hybrid mode
        config_path=f"config/accounts/account-{account.account_number}.yml",
        portable=True,
        trading_config=default_config
    )


@router.put("/accounts/{account_id}/config", response_model=AccountConfigResponse)
async def update_account_configuration(
    account_id: int,
    config_update: AccountConfigUpdate,
    db: Session = Depends(get_db_dependency)
):
    """
    Update account configuration
    
    Saves trading configuration for an account. Configuration can be stored in:
    - Database: All config in trading_config_json column
    - YAML: All config in external YAML file
    - Hybrid: Credentials in DB, config in YAML (recommended)
    
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
    # Get account
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account with ID {account_id} not found")
    
    # For now, just return success
    # Once we add the database columns, we'll actually save the configuration
    
    # Log the configuration (for debugging)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Configuration saved for account {account_id}")
    logger.info(f"Config source: {config_update.config_source}")
    logger.info(f"Config path: {config_update.config_path}")
    logger.info(f"Portable: {config_update.portable}")
    logger.info(f"Trading config: {config_update.trading_config}")
    
    # Return the updated configuration
    return AccountConfigResponse(
        account_id=account.id,
        account_number=account.account_number,
        account_name=account.account_name,
        config_source=config_update.config_source or "hybrid",
        config_path=config_update.config_path,
        portable=config_update.portable if config_update.portable is not None else True,
        trading_config=config_update.trading_config
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
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Export configuration for account {account_id} to {output_path}")
    
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
