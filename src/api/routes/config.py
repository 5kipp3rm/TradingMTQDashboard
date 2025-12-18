"""
Configuration API Endpoints
Exposes ConfigManager to UI and CLI
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.services.config_manager import (
    get_config_manager,
    CurrencyConfig,
    TradingPreferences
)

router = APIRouter(prefix="/api/config", tags=["Configuration"])


# Request/Response Models

class CurrencyResponse(BaseModel):
    symbol: str
    description: str
    category: str
    digits: int
    point: float
    contract_size: int
    min_lot: float
    max_lot: float
    lot_step: float
    spread_typical: float
    enabled: bool
    custom: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CurrencyCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    description: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=50)
    digits: int = Field(..., ge=0, le=8)
    point: float = Field(..., gt=0)
    contract_size: int = Field(..., gt=0)
    min_lot: float = Field(default=0.01, gt=0)
    max_lot: float = Field(default=100.0, gt=0)
    lot_step: float = Field(default=0.01, gt=0)
    spread_typical: float = Field(default=0.0, ge=0)
    enabled: bool = True


class PreferencesResponse(BaseModel):
    default_volume: float
    default_sl_pips: Optional[float]
    default_tp_pips: Optional[float]
    max_risk_percent: float
    max_daily_loss_percent: float
    max_positions: int
    favorite_symbols: List[str]
    recent_symbols: List[str]
    max_recent: int


class PreferencesUpdateRequest(BaseModel):
    default_volume: Optional[float] = Field(None, gt=0)
    default_sl_pips: Optional[float] = Field(None, gt=0)
    default_tp_pips: Optional[float] = Field(None, gt=0)
    max_risk_percent: Optional[float] = Field(None, gt=0, le=100)
    max_daily_loss_percent: Optional[float] = Field(None, gt=0, le=100)
    max_positions: Optional[int] = Field(None, gt=0)


class FavoriteRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)


# Currency Endpoints

@router.get("/currencies", response_model=List[CurrencyResponse])
async def get_currencies(
    enabled_only: bool = False,
    category: Optional[str] = None
):
    """
    Get all currencies

    Query parameters:
    - enabled_only: Return only enabled currencies
    - category: Filter by category
    """
    config_manager = get_config_manager()

    if category:
        currencies = config_manager.get_currencies_by_category(category, enabled_only)
    else:
        currencies = config_manager.get_all_currencies(enabled_only)

    return [CurrencyResponse(**curr.to_dict()) for curr in currencies]


@router.get("/currencies/{symbol}", response_model=CurrencyResponse)
async def get_currency(symbol: str):
    """Get specific currency by symbol"""
    config_manager = get_config_manager()
    currency = config_manager.get_currency(symbol)

    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currency not found: {symbol}"
        )

    return CurrencyResponse(**currency.to_dict())


@router.post("/currencies", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED)
async def create_currency(request: CurrencyCreateRequest):
    """Create or update currency"""
    config_manager = get_config_manager()

    currency = CurrencyConfig(
        symbol=request.symbol.upper(),
        description=request.description,
        category=request.category,
        digits=request.digits,
        point=request.point,
        contract_size=request.contract_size,
        min_lot=request.min_lot,
        max_lot=request.max_lot,
        lot_step=request.lot_step,
        spread_typical=request.spread_typical,
        enabled=request.enabled,
        custom=True
    )

    success = config_manager.add_currency(currency)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create currency"
        )

    return CurrencyResponse(**currency.to_dict())


@router.delete("/currencies/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_currency(symbol: str):
    """Delete custom currency (default currencies cannot be deleted)"""
    config_manager = get_config_manager()

    success = config_manager.remove_currency(symbol)
    if not success:
        currency = config_manager.get_currency(symbol)
        if not currency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Currency not found: {symbol}"
            )
        if not currency.custom:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete default currency: {symbol}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete currency"
        )


@router.post("/currencies/{symbol}/enable", response_model=CurrencyResponse)
async def enable_currency(symbol: str):
    """Enable a currency"""
    config_manager = get_config_manager()

    success = config_manager.enable_currency(symbol)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currency not found: {symbol}"
        )

    currency = config_manager.get_currency(symbol)
    return CurrencyResponse(**currency.to_dict())


@router.post("/currencies/{symbol}/disable", response_model=CurrencyResponse)
async def disable_currency(symbol: str):
    """Disable a currency"""
    config_manager = get_config_manager()

    success = config_manager.disable_currency(symbol)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currency not found: {symbol}"
        )

    currency = config_manager.get_currency(symbol)
    return CurrencyResponse(**currency.to_dict())


@router.get("/categories", response_model=List[str])
async def get_categories():
    """Get all available currency categories"""
    config_manager = get_config_manager()
    return config_manager.get_categories()


# Trading Preferences Endpoints

@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences():
    """Get trading preferences"""
    config_manager = get_config_manager()
    prefs = config_manager.get_preferences()
    return PreferencesResponse(**prefs.to_dict())


@router.put("/preferences", response_model=PreferencesResponse)
async def update_preferences(request: PreferencesUpdateRequest):
    """Update trading preferences"""
    config_manager = get_config_manager()

    # Extract non-None values
    updates = {k: v for k, v in request.dict().items() if v is not None}

    success = config_manager.update_preferences(**updates)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

    prefs = config_manager.get_preferences()
    return PreferencesResponse(**prefs.to_dict())


# Favorites Endpoints

@router.get("/favorites", response_model=List[CurrencyResponse])
async def get_favorites():
    """Get favorite currencies"""
    config_manager = get_config_manager()
    favorites = config_manager.get_favorites()
    return [CurrencyResponse(**curr.to_dict()) for curr in favorites]


@router.post("/favorites", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(request: FavoriteRequest):
    """Add symbol to favorites"""
    config_manager = get_config_manager()

    # Verify currency exists
    currency = config_manager.get_currency(request.symbol)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currency not found: {request.symbol}"
        )

    success = config_manager.add_favorite(request.symbol)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add favorite"
        )


@router.delete("/favorites/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(symbol: str):
    """Remove symbol from favorites"""
    config_manager = get_config_manager()

    success = config_manager.remove_favorite(symbol)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove favorite"
        )


# Recent Currencies Endpoints

@router.get("/recent", response_model=List[CurrencyResponse])
async def get_recent():
    """Get recently used currencies"""
    config_manager = get_config_manager()
    recent = config_manager.get_recent()
    return [CurrencyResponse(**curr.to_dict()) for curr in recent]


@router.post("/recent", status_code=status.HTTP_204_NO_CONTENT)
async def add_recent(request: FavoriteRequest):
    """Add symbol to recent list"""
    config_manager = get_config_manager()

    # Verify currency exists
    currency = config_manager.get_currency(request.symbol)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currency not found: {request.symbol}"
        )

    success = config_manager.add_recent(request.symbol)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add to recent"
        )


# Statistics and Export/Import

@router.get("/stats", response_model=Dict[str, Any])
async def get_stats():
    """Get configuration statistics"""
    config_manager = get_config_manager()
    return config_manager.get_stats()


@router.post("/export")
async def export_config(file_path: str):
    """Export configuration to file"""
    config_manager = get_config_manager()

    try:
        path = Path(file_path)
        success = config_manager.export_config(path)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export configuration"
            )
        return {"message": f"Configuration exported to {file_path}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/import")
async def import_config(file_path: str, merge: bool = True):
    """Import configuration from file"""
    config_manager = get_config_manager()

    try:
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )

        success = config_manager.import_config(path, merge=merge)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to import configuration"
            )

        return {"message": f"Configuration imported from {file_path}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_config():
    """Reset configuration to defaults"""
    config_manager = get_config_manager()
    config_manager.currencies.clear()
    config_manager._initialize_defaults()
    config_manager.save()
