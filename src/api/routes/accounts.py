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

from src.database import get_session, TradingAccount, AccountConnectionState, PlatformType
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
    db: Session = Depends(get_session)
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
    db: Session = Depends(get_session)
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
    db: Session = Depends(get_session)
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
    db: Session = Depends(get_session)
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
    db: Session = Depends(get_session)
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
    db: Session = Depends(get_session)
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
    db: Session = Depends(get_session)
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
    db: Session = Depends(get_session)
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
