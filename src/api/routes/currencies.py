"""
Currency Configuration Management API

Provides REST endpoints for managing currency pair trading configurations.
Supports CRUD operations, enable/disable, hot-reload, and YAML export/import.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from datetime import datetime

from src.database import get_session, CurrencyConfiguration


router = APIRouter()


# ============================================================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE
# ============================================================================

class CurrencyConfigCreate(BaseModel):
    """Request model for creating a new currency configuration"""

    symbol: str = Field(..., description="Currency pair symbol (e.g., EURUSD)", min_length=6, max_length=20)
    enabled: bool = Field(True, description="Whether this currency is enabled for trading")

    # Risk Management
    risk_percent: float = Field(..., description="Risk per trade as % of account", ge=0.1, le=10.0)
    max_position_size: float = Field(..., description="Maximum position size in lots", gt=0)
    min_position_size: float = Field(..., description="Minimum position size in lots", gt=0)

    # Strategy
    strategy_type: str = Field(..., description="Strategy type: 'crossover' or 'position'")
    timeframe: str = Field(..., description="Trading timeframe: M1, M5, M15, M30, H1, H4, D1, W1")

    # Technical Indicators
    fast_period: int = Field(..., description="Fast MA period", gt=0)
    slow_period: int = Field(..., description="Slow MA period", gt=0)

    # Stop Loss / Take Profit
    sl_pips: int = Field(..., description="Stop Loss in pips", gt=0)
    tp_pips: int = Field(..., description="Take Profit in pips", gt=0)

    # Trading Rules
    cooldown_seconds: int = Field(..., description="Cooldown between trades in seconds", ge=0)
    trade_on_signal_change: bool = Field(True, description="Require signal change before re-entry")

    # Position Stacking
    allow_position_stacking: bool = Field(False, description="Allow multiple positions in same direction")
    max_positions_same_direction: int = Field(1, description="Max positions in same direction", ge=1)
    max_total_positions: int = Field(5, description="Max total positions for this symbol", ge=1)
    stacking_risk_multiplier: float = Field(1.0, description="Risk multiplier for additional positions", gt=0)

    # Trading Hours (optional)
    trading_hours_start: Optional[str] = Field(None, description="Trading hours start (HH:MM UTC)")
    trading_hours_end: Optional[str] = Field(None, description="Trading hours end (HH:MM UTC)")

    # Additional
    description: Optional[str] = Field(None, description="Configuration description", max_length=1000)
    additional_settings: Optional[dict] = Field(None, description="Additional settings as JSON")

    @validator('symbol')
    def symbol_uppercase(cls, v):
        """Ensure symbol is uppercase"""
        return v.upper().strip()

    @validator('strategy_type')
    def validate_strategy_type(cls, v):
        """Validate strategy type"""
        if v.lower() not in ['crossover', 'position']:
            raise ValueError("Strategy type must be 'crossover' or 'position'")
        return v.lower()

    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe"""
        valid_timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']
        if v.upper() not in valid_timeframes:
            raise ValueError(f"Timeframe must be one of: {', '.join(valid_timeframes)}")
        return v.upper()

    @validator('slow_period')
    def validate_periods(cls, v, values):
        """Ensure slow period > fast period"""
        if 'fast_period' in values and v <= values['fast_period']:
            raise ValueError("Slow period must be greater than fast period")
        return v

    @validator('max_position_size')
    def validate_position_sizes(cls, v, values):
        """Ensure max >= min"""
        if 'min_position_size' in values and v < values['min_position_size']:
            raise ValueError("Max position size must be >= min position size")
        return v

    @validator('trading_hours_start', 'trading_hours_end')
    def validate_time_format(cls, v):
        """Validate HH:MM format"""
        if v is None:
            return v

        if len(v) != 5 or v[2] != ':':
            raise ValueError("Time must be in HH:MM format")

        try:
            hours, minutes = v.split(':')
            h = int(hours)
            m = int(minutes)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError("Invalid time range")
        except (ValueError, AttributeError):
            raise ValueError("Time must be in HH:MM format (00:00 - 23:59)")

        return v


class CurrencyConfigUpdate(BaseModel):
    """Request model for updating an existing currency configuration"""

    enabled: Optional[bool] = None

    # Risk Management
    risk_percent: Optional[float] = Field(None, ge=0.1, le=10.0)
    max_position_size: Optional[float] = Field(None, gt=0)
    min_position_size: Optional[float] = Field(None, gt=0)

    # Strategy
    strategy_type: Optional[str] = None
    timeframe: Optional[str] = None

    # Technical Indicators
    fast_period: Optional[int] = Field(None, gt=0)
    slow_period: Optional[int] = Field(None, gt=0)

    # Stop Loss / Take Profit
    sl_pips: Optional[int] = Field(None, gt=0)
    tp_pips: Optional[int] = Field(None, gt=0)

    # Trading Rules
    cooldown_seconds: Optional[int] = Field(None, ge=0)
    trade_on_signal_change: Optional[bool] = None

    # Position Stacking
    allow_position_stacking: Optional[bool] = None
    max_positions_same_direction: Optional[int] = Field(None, ge=1)
    max_total_positions: Optional[int] = Field(None, ge=1)
    stacking_risk_multiplier: Optional[float] = Field(None, gt=0)

    # Trading Hours
    trading_hours_start: Optional[str] = None
    trading_hours_end: Optional[str] = None

    # Additional
    description: Optional[str] = Field(None, max_length=1000)
    additional_settings: Optional[dict] = None

    @validator('strategy_type')
    def validate_strategy_type(cls, v):
        """Validate strategy type"""
        if v and v.lower() not in ['crossover', 'position']:
            raise ValueError("Strategy type must be 'crossover' or 'position'")
        return v.lower() if v else None

    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe"""
        if v is None:
            return v
        valid_timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']
        if v.upper() not in valid_timeframes:
            raise ValueError(f"Timeframe must be one of: {', '.join(valid_timeframes)}")
        return v.upper()

    @validator('trading_hours_start', 'trading_hours_end')
    def validate_time_format(cls, v):
        """Validate HH:MM format"""
        if v is None:
            return v

        if len(v) != 5 or v[2] != ':':
            raise ValueError("Time must be in HH:MM format")

        try:
            hours, minutes = v.split(':')
            h = int(hours)
            m = int(minutes)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError("Invalid time range")
        except (ValueError, AttributeError):
            raise ValueError("Time must be in HH:MM format (00:00 - 23:59)")

        return v


class CurrencyConfigResponse(BaseModel):
    """Response model for currency configuration"""

    id: int
    symbol: str
    enabled: bool

    # Risk Management
    risk_percent: float
    max_position_size: float
    min_position_size: float

    # Strategy
    strategy_type: str
    timeframe: str

    # Technical Indicators
    fast_period: int
    slow_period: int

    # Stop Loss / Take Profit
    sl_pips: int
    tp_pips: int

    # Trading Rules
    cooldown_seconds: int
    trade_on_signal_change: bool

    # Position Stacking
    allow_position_stacking: bool
    max_positions_same_direction: int
    max_total_positions: int
    stacking_risk_multiplier: float

    # Trading Hours
    trading_hours_start: Optional[str]
    trading_hours_end: Optional[str]

    # Additional
    description: Optional[str]
    additional_settings: Optional[dict]
    config_version: int

    # Audit Trail
    created_at: str
    updated_at: str
    last_loaded: Optional[str]

    class Config:
        from_attributes = True


class CurrencyConfigListResponse(BaseModel):
    """Response model for list of currency configurations"""

    currencies: List[CurrencyConfigResponse]
    total: int
    enabled_count: int


class ValidationError(BaseModel):
    """Validation error details"""

    field: str
    message: str


class CurrencyValidationResponse(BaseModel):
    """Response model for configuration validation"""

    is_valid: bool
    errors: List[str]
    symbol: str


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/currencies", response_model=CurrencyConfigListResponse)
async def list_currencies(
    enabled_only: bool = Query(False, description="Show only enabled currencies"),
    db: Session = Depends(get_session)
):
    """
    List all currency configurations.

    Returns list of all configured currency pairs with their trading settings.
    Optionally filter to show only enabled currencies.
    """
    query = select(CurrencyConfiguration)

    if enabled_only:
        query = query.where(CurrencyConfiguration.enabled == True)

    query = query.order_by(CurrencyConfiguration.symbol)

    result = db.execute(query)
    currencies = result.scalars().all()

    # Count enabled currencies
    enabled_count = sum(1 for c in currencies if c.enabled)

    return CurrencyConfigListResponse(
        currencies=[
            CurrencyConfigResponse(
                id=c.id,
                symbol=c.symbol,
                enabled=c.enabled,
                risk_percent=c.risk_percent,
                max_position_size=c.max_position_size,
                min_position_size=c.min_position_size,
                strategy_type=c.strategy_type,
                timeframe=c.timeframe,
                fast_period=c.fast_period,
                slow_period=c.slow_period,
                sl_pips=c.sl_pips,
                tp_pips=c.tp_pips,
                cooldown_seconds=c.cooldown_seconds,
                trade_on_signal_change=c.trade_on_signal_change,
                allow_position_stacking=c.allow_position_stacking,
                max_positions_same_direction=c.max_positions_same_direction,
                max_total_positions=c.max_total_positions,
                stacking_risk_multiplier=c.stacking_risk_multiplier,
                trading_hours_start=c.trading_hours_start,
                trading_hours_end=c.trading_hours_end,
                description=c.description,
                additional_settings=c.additional_settings,
                config_version=c.config_version,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
                last_loaded=c.last_loaded.isoformat() if c.last_loaded else None
            )
            for c in currencies
        ],
        total=len(currencies),
        enabled_count=enabled_count
    )


@router.get("/currencies/{symbol}", response_model=CurrencyConfigResponse)
async def get_currency(
    symbol: str,
    db: Session = Depends(get_session)
):
    """
    Get specific currency configuration by symbol.

    Returns detailed configuration for a single currency pair.
    """
    symbol = symbol.upper()

    currency = db.execute(
        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == symbol)
    ).scalar_one_or_none()

    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency {symbol} not found")

    return CurrencyConfigResponse(
        id=currency.id,
        symbol=currency.symbol,
        enabled=currency.enabled,
        risk_percent=currency.risk_percent,
        max_position_size=currency.max_position_size,
        min_position_size=currency.min_position_size,
        strategy_type=currency.strategy_type,
        timeframe=currency.timeframe,
        fast_period=currency.fast_period,
        slow_period=currency.slow_period,
        sl_pips=currency.sl_pips,
        tp_pips=currency.tp_pips,
        cooldown_seconds=currency.cooldown_seconds,
        trade_on_signal_change=currency.trade_on_signal_change,
        allow_position_stacking=currency.allow_position_stacking,
        max_positions_same_direction=currency.max_positions_same_direction,
        max_total_positions=currency.max_total_positions,
        stacking_risk_multiplier=currency.stacking_risk_multiplier,
        trading_hours_start=currency.trading_hours_start,
        trading_hours_end=currency.trading_hours_end,
        description=currency.description,
        additional_settings=currency.additional_settings,
        config_version=currency.config_version,
        created_at=currency.created_at.isoformat(),
        updated_at=currency.updated_at.isoformat(),
        last_loaded=currency.last_loaded.isoformat() if currency.last_loaded else None
    )


@router.post("/currencies", response_model=CurrencyConfigResponse, status_code=201)
async def create_currency(
    config_data: CurrencyConfigCreate,
    db: Session = Depends(get_session)
):
    """
    Create a new currency configuration.

    Creates a new trading configuration for a currency pair.
    Validates all settings before saving.
    """
    # Check if currency already exists
    existing = db.execute(
        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == config_data.symbol)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Currency {config_data.symbol} already exists"
        )

    # Create new configuration
    new_config = CurrencyConfiguration(
        symbol=config_data.symbol,
        enabled=config_data.enabled,
        risk_percent=config_data.risk_percent,
        max_position_size=config_data.max_position_size,
        min_position_size=config_data.min_position_size,
        strategy_type=config_data.strategy_type,
        timeframe=config_data.timeframe,
        fast_period=config_data.fast_period,
        slow_period=config_data.slow_period,
        sl_pips=config_data.sl_pips,
        tp_pips=config_data.tp_pips,
        cooldown_seconds=config_data.cooldown_seconds,
        trade_on_signal_change=config_data.trade_on_signal_change,
        allow_position_stacking=config_data.allow_position_stacking,
        max_positions_same_direction=config_data.max_positions_same_direction,
        max_total_positions=config_data.max_total_positions,
        stacking_risk_multiplier=config_data.stacking_risk_multiplier,
        trading_hours_start=config_data.trading_hours_start,
        trading_hours_end=config_data.trading_hours_end,
        description=config_data.description,
        additional_settings=config_data.additional_settings
    )

    # Validate configuration
    is_valid, errors = new_config.validate()
    if not is_valid:
        raise HTTPException(status_code=400, detail={"errors": errors})

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    return CurrencyConfigResponse(
        id=new_config.id,
        symbol=new_config.symbol,
        enabled=new_config.enabled,
        risk_percent=new_config.risk_percent,
        max_position_size=new_config.max_position_size,
        min_position_size=new_config.min_position_size,
        strategy_type=new_config.strategy_type,
        timeframe=new_config.timeframe,
        fast_period=new_config.fast_period,
        slow_period=new_config.slow_period,
        sl_pips=new_config.sl_pips,
        tp_pips=new_config.tp_pips,
        cooldown_seconds=new_config.cooldown_seconds,
        trade_on_signal_change=new_config.trade_on_signal_change,
        allow_position_stacking=new_config.allow_position_stacking,
        max_positions_same_direction=new_config.max_positions_same_direction,
        max_total_positions=new_config.max_total_positions,
        stacking_risk_multiplier=new_config.stacking_risk_multiplier,
        trading_hours_start=new_config.trading_hours_start,
        trading_hours_end=new_config.trading_hours_end,
        description=new_config.description,
        additional_settings=new_config.additional_settings,
        config_version=new_config.config_version,
        created_at=new_config.created_at.isoformat(),
        updated_at=new_config.updated_at.isoformat(),
        last_loaded=new_config.last_loaded.isoformat() if new_config.last_loaded else None
    )


@router.put("/currencies/{symbol}", response_model=CurrencyConfigResponse)
async def update_currency(
    symbol: str,
    config_data: CurrencyConfigUpdate,
    db: Session = Depends(get_session)
):
    """
    Update an existing currency configuration.

    Updates configuration for an existing currency pair.
    Only provided fields are updated.
    Increments config_version on each update.
    """
    symbol = symbol.upper()

    currency = db.execute(
        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == symbol)
    ).scalar_one_or_none()

    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency {symbol} not found")

    # Update only provided fields
    update_data = config_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(currency, field, value)

    # Increment version
    currency.config_version += 1
    currency.updated_at = datetime.utcnow()

    # Validate updated configuration
    is_valid, errors = currency.validate()
    if not is_valid:
        db.rollback()
        raise HTTPException(status_code=400, detail={"errors": errors})

    db.commit()
    db.refresh(currency)

    return CurrencyConfigResponse(
        id=currency.id,
        symbol=currency.symbol,
        enabled=currency.enabled,
        risk_percent=currency.risk_percent,
        max_position_size=currency.max_position_size,
        min_position_size=currency.min_position_size,
        strategy_type=currency.strategy_type,
        timeframe=currency.timeframe,
        fast_period=currency.fast_period,
        slow_period=currency.slow_period,
        sl_pips=currency.sl_pips,
        tp_pips=currency.tp_pips,
        cooldown_seconds=currency.cooldown_seconds,
        trade_on_signal_change=currency.trade_on_signal_change,
        allow_position_stacking=currency.allow_position_stacking,
        max_positions_same_direction=currency.max_positions_same_direction,
        max_total_positions=currency.max_total_positions,
        stacking_risk_multiplier=currency.stacking_risk_multiplier,
        trading_hours_start=currency.trading_hours_start,
        trading_hours_end=currency.trading_hours_end,
        description=currency.description,
        additional_settings=currency.additional_settings,
        config_version=currency.config_version,
        created_at=currency.created_at.isoformat(),
        updated_at=currency.updated_at.isoformat(),
        last_loaded=currency.last_loaded.isoformat() if currency.last_loaded else None
    )


@router.delete("/currencies/{symbol}", status_code=204)
async def delete_currency(
    symbol: str,
    db: Session = Depends(get_session)
):
    """
    Delete a currency configuration.

    Deletes a currency configuration. Note: This does not delete
    associated trades - they will remain in the database.
    """
    symbol = symbol.upper()

    currency = db.execute(
        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == symbol)
    ).scalar_one_or_none()

    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency {symbol} not found")

    db.delete(currency)
    db.commit()

    return None


@router.post("/currencies/{symbol}/enable", response_model=CurrencyConfigResponse)
async def enable_currency(
    symbol: str,
    db: Session = Depends(get_session)
):
    """
    Enable a currency for trading.

    Sets the currency as enabled, allowing it to be traded.
    """
    symbol = symbol.upper()

    currency = db.execute(
        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == symbol)
    ).scalar_one_or_none()

    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency {symbol} not found")

    currency.enabled = True
    currency.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(currency)

    return CurrencyConfigResponse(
        id=currency.id,
        symbol=currency.symbol,
        enabled=currency.enabled,
        risk_percent=currency.risk_percent,
        max_position_size=currency.max_position_size,
        min_position_size=currency.min_position_size,
        strategy_type=currency.strategy_type,
        timeframe=currency.timeframe,
        fast_period=currency.fast_period,
        slow_period=currency.slow_period,
        sl_pips=currency.sl_pips,
        tp_pips=currency.tp_pips,
        cooldown_seconds=currency.cooldown_seconds,
        trade_on_signal_change=currency.trade_on_signal_change,
        allow_position_stacking=currency.allow_position_stacking,
        max_positions_same_direction=currency.max_positions_same_direction,
        max_total_positions=currency.max_total_positions,
        stacking_risk_multiplier=currency.stacking_risk_multiplier,
        trading_hours_start=currency.trading_hours_start,
        trading_hours_end=currency.trading_hours_end,
        description=currency.description,
        additional_settings=currency.additional_settings,
        config_version=currency.config_version,
        created_at=currency.created_at.isoformat(),
        updated_at=currency.updated_at.isoformat(),
        last_loaded=currency.last_loaded.isoformat() if currency.last_loaded else None
    )


@router.post("/currencies/{symbol}/disable", response_model=CurrencyConfigResponse)
async def disable_currency(
    symbol: str,
    db: Session = Depends(get_session)
):
    """
    Disable a currency for trading.

    Sets the currency as disabled, preventing it from being traded.
    """
    symbol = symbol.upper()

    currency = db.execute(
        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == symbol)
    ).scalar_one_or_none()

    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency {symbol} not found")

    currency.enabled = False
    currency.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(currency)

    return CurrencyConfigResponse(
        id=currency.id,
        symbol=currency.symbol,
        enabled=currency.enabled,
        risk_percent=currency.risk_percent,
        max_position_size=currency.max_position_size,
        min_position_size=currency.min_position_size,
        strategy_type=currency.strategy_type,
        timeframe=currency.timeframe,
        fast_period=currency.fast_period,
        slow_period=currency.slow_period,
        sl_pips=currency.sl_pips,
        tp_pips=currency.tp_pips,
        cooldown_seconds=currency.cooldown_seconds,
        trade_on_signal_change=currency.trade_on_signal_change,
        allow_position_stacking=currency.allow_position_stacking,
        max_positions_same_direction=currency.max_positions_same_direction,
        max_total_positions=currency.max_total_positions,
        stacking_risk_multiplier=currency.stacking_risk_multiplier,
        trading_hours_start=currency.trading_hours_start,
        trading_hours_end=currency.trading_hours_end,
        description=currency.description,
        additional_settings=currency.additional_settings,
        config_version=currency.config_version,
        created_at=currency.created_at.isoformat(),
        updated_at=currency.updated_at.isoformat(),
        last_loaded=currency.last_loaded.isoformat() if currency.last_loaded else None
    )


@router.post("/currencies/validate", response_model=CurrencyValidationResponse)
async def validate_currency_config(
    config_data: CurrencyConfigCreate,
    db: Session = Depends(get_session)
):
    """
    Validate a currency configuration without saving.

    Validates all settings and returns any errors found.
    Useful for client-side validation before submission.
    """
    # Create temporary config for validation
    temp_config = CurrencyConfiguration(
        symbol=config_data.symbol,
        enabled=config_data.enabled,
        risk_percent=config_data.risk_percent,
        max_position_size=config_data.max_position_size,
        min_position_size=config_data.min_position_size,
        strategy_type=config_data.strategy_type,
        timeframe=config_data.timeframe,
        fast_period=config_data.fast_period,
        slow_period=config_data.slow_period,
        sl_pips=config_data.sl_pips,
        tp_pips=config_data.tp_pips,
        cooldown_seconds=config_data.cooldown_seconds,
        trade_on_signal_change=config_data.trade_on_signal_change,
        allow_position_stacking=config_data.allow_position_stacking,
        max_positions_same_direction=config_data.max_positions_same_direction,
        max_total_positions=config_data.max_total_positions,
        stacking_risk_multiplier=config_data.stacking_risk_multiplier,
        trading_hours_start=config_data.trading_hours_start,
        trading_hours_end=config_data.trading_hours_end,
        description=config_data.description,
        additional_settings=config_data.additional_settings
    )

    is_valid, errors = temp_config.validate()

    return CurrencyValidationResponse(
        is_valid=is_valid,
        errors=errors,
        symbol=config_data.symbol
    )
