"""
Configuration Validation Schemas for TradingMTQ

Provides Pydantic models for validating all configuration files and parameters.
Ensures type safety, value ranges, and required fields before the system starts.

Features:
- Type validation (int, float, str, bool, enums)
- Range validation (min/max values)
- Required field validation
- Custom validators for complex rules
- Clear error messages on validation failure

Usage:
    from src.config.schemas import TradingConfig, CurrencyConfig

    # Load and validate YAML config
    with open('config/currencies.yaml') as f:
        raw_config = yaml.safe_load(f)

    # Validate with Pydantic
    config = TradingConfig(**raw_config)  # Raises ValidationError if invalid

    # Access validated config
    print(config.max_concurrent_trades)  # Type-safe access
"""
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Any
from enum import Enum
import re


# =============================================================================
# Enums for Type Safety
# =============================================================================

class OrderType(str, Enum):
    """Supported order types"""
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


class TimeFrame(str, Enum):
    """Supported timeframes"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"


class StrategyType(str, Enum):
    """Supported strategy types"""
    SIMPLE_MA = "simple_ma"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    MULTI_INDICATOR = "multi_indicator"
    ML_STRATEGY = "ml_strategy"


# =============================================================================
# MT5 Connection Configuration
# =============================================================================

class MT5ConnectionConfig(BaseModel):
    """MT5 connection parameters"""

    login: int = Field(..., description="MT5 account number")
    password: str = Field(..., min_length=1, description="MT5 account password")
    server: str = Field(..., min_length=1, description="Broker server name")
    timeout: int = Field(60000, ge=5000, le=300000, description="Connection timeout (ms)")
    portable: bool = Field(False, description="Use portable mode")

    @validator('login')
    def validate_login(cls, v):
        """Validate login is positive"""
        if v <= 0:
            raise ValueError("Login must be a positive integer")
        return v

    @validator('server')
    def validate_server(cls, v):
        """Validate server format"""
        # Basic validation - server name should not be empty or contain invalid chars
        if not v or not re.match(r'^[\w\-\.]+$', v):
            raise ValueError(
                "Server name must contain only alphanumeric characters, hyphens, and dots"
            )
        return v

    class Config:
        extra = "forbid"  # Don't allow extra fields


# =============================================================================
# Currency/Symbol Configuration
# =============================================================================

class CurrencyConfig(BaseModel):
    """Configuration for a single currency pair"""

    symbol: str = Field(..., min_length=6, max_length=12, description="Currency pair symbol")
    enabled: bool = Field(True, description="Whether trading is enabled for this pair")

    # Strategy configuration
    strategy: StrategyType = Field(..., description="Strategy to use")
    timeframe: TimeFrame = Field(TimeFrame.H1, description="Trading timeframe")

    # Risk management
    risk_percent: float = Field(2.0, ge=0.1, le=10.0, description="Risk per trade (%)")
    max_positions: int = Field(3, ge=1, le=10, description="Max concurrent positions")

    # Order parameters
    use_position_trading: bool = Field(True, description="Use position trading mode")
    check_interval_seconds: int = Field(30, ge=10, le=300, description="Check interval")

    # Stop loss & Take profit
    use_fixed_sl: bool = Field(False, description="Use fixed SL instead of ATR")
    fixed_sl_pips: Optional[float] = Field(None, ge=5, le=500, description="Fixed SL in pips")
    use_fixed_tp: bool = Field(False, description="Use fixed TP instead of ATR")
    fixed_tp_pips: Optional[float] = Field(None, ge=5, le=1000, description="Fixed TP in pips")

    # ATR-based SL/TP
    atr_period: int = Field(14, ge=5, le=50, description="ATR period")
    atr_sl_multiplier: float = Field(2.0, ge=0.5, le=5.0, description="ATR SL multiplier")
    atr_tp_multiplier: float = Field(3.0, ge=1.0, le=10.0, description="ATR TP multiplier")

    # Automatic SL/TP management
    enable_breakeven: bool = Field(True, description="Enable breakeven stop loss")
    breakeven_trigger_pips: float = Field(15.0, ge=5.0, le=100.0,
                                          description="Pips profit to trigger breakeven")
    breakeven_offset_pips: float = Field(2.0, ge=0.0, le=20.0,
                                        description="Offset above breakeven")

    enable_trailing: bool = Field(True, description="Enable trailing stop loss")
    trailing_start_pips: float = Field(20.0, ge=10.0, le=200.0,
                                       description="Pips profit to start trailing")
    trailing_distance_pips: float = Field(10.0, ge=5.0, le=100.0,
                                          description="Trailing distance in pips")

    enable_partial_close: bool = Field(False, description="Enable partial position closure")
    partial_close_percent: float = Field(50.0, ge=10.0, le=90.0,
                                         description="Percentage to close")
    partial_close_profit_pips: float = Field(25.0, ge=10.0, le=200.0,
                                             description="Profit to trigger partial close")

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate symbol format (typically 6 characters like EURUSD)"""
        if not re.match(r'^[A-Z]{6,12}$', v):
            raise ValueError(
                f"Symbol '{v}' must be 6-12 uppercase letters (e.g., EURUSD, GBPUSD)"
            )
        return v

    @root_validator
    def validate_sl_tp_config(cls, values):
        """Validate SL/TP configuration consistency"""
        use_fixed_sl = values.get('use_fixed_sl')
        fixed_sl_pips = values.get('fixed_sl_pips')
        use_fixed_tp = values.get('use_fixed_tp')
        fixed_tp_pips = values.get('fixed_tp_pips')

        # If using fixed SL, must provide pips value
        if use_fixed_sl and (fixed_sl_pips is None or fixed_sl_pips <= 0):
            raise ValueError("fixed_sl_pips must be provided when use_fixed_sl is True")

        # If using fixed TP, must provide pips value
        if use_fixed_tp and (fixed_tp_pips is None or fixed_tp_pips <= 0):
            raise ValueError("fixed_tp_pips must be provided when use_fixed_tp is True")

        return values

    class Config:
        extra = "forbid"
        use_enum_values = True


# =============================================================================
# Portfolio/Orchestrator Configuration
# =============================================================================

class TradingConfig(BaseModel):
    """Main trading configuration"""

    # Portfolio limits
    max_concurrent_trades: int = Field(15, ge=1, le=100,
                                       description="Maximum concurrent positions across all pairs")
    portfolio_risk_percent: float = Field(8.0, ge=1.0, le=20.0,
                                          description="Total portfolio risk (%)")

    # Intelligent position manager
    use_intelligent_manager: bool = Field(True,
                                          description="Use AI-powered position management")

    # Hot-reload configuration
    hot_reload_enabled: bool = Field(True,
                                     description="Enable hot-reload of config changes")
    hot_reload_interval_seconds: int = Field(60, ge=30, le=600,
                                             description="Config reload check interval")

    # Parallel execution
    parallel_execution: bool = Field(False,
                                     description="Execute currency traders in parallel")

    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_to_file: bool = Field(True, description="Enable file logging")
    log_to_console: bool = Field(True, description="Enable console logging")

    # ML/LLM features
    enable_ml: bool = Field(False, description="Enable ML enhancement")
    enable_llm: bool = Field(False, description="Enable LLM sentiment analysis")

    # Currency configurations
    currencies: List[CurrencyConfig] = Field(..., min_items=1,
                                             description="List of currency configurations")

    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @validator('currencies')
    def validate_unique_symbols(cls, v):
        """Ensure no duplicate symbols"""
        symbols = [c.symbol for c in v]
        if len(symbols) != len(set(symbols)):
            duplicates = [s for s in symbols if symbols.count(s) > 1]
            raise ValueError(f"Duplicate symbols found: {set(duplicates)}")
        return v

    class Config:
        extra = "forbid"


# =============================================================================
# ML/LLM Configuration
# =============================================================================

class MLConfig(BaseModel):
    """Machine Learning configuration"""

    model_type: str = Field("lstm", description="Model type (lstm, random_forest)")
    model_path: Optional[str] = Field(None, description="Path to trained model")
    feature_window: int = Field(50, ge=10, le=200, description="Feature window size")
    confidence_threshold: float = Field(0.6, ge=0.0, le=1.0,
                                       description="Minimum confidence for signals")
    enable_feature_scaling: bool = Field(True, description="Enable feature scaling")

    @validator('model_type')
    def validate_model_type(cls, v):
        """Validate model type"""
        valid_types = ['lstm', 'random_forest', 'xgboost', 'ensemble']
        if v.lower() not in valid_types:
            raise ValueError(f"model_type must be one of {valid_types}")
        return v.lower()

    class Config:
        extra = "forbid"


class LLMConfig(BaseModel):
    """LLM API configuration"""

    provider: str = Field("openai", description="LLM provider (openai, anthropic)")
    api_key: str = Field(..., min_length=10, description="API key")
    model: str = Field("gpt-4o", description="Model name")
    max_tokens: int = Field(500, ge=50, le=2000, description="Max tokens per request")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    enable_caching: bool = Field(True, description="Enable response caching")

    @validator('provider')
    def validate_provider(cls, v):
        """Validate LLM provider"""
        valid_providers = ['openai', 'anthropic', 'ollama']
        if v.lower() not in valid_providers:
            raise ValueError(f"provider must be one of {valid_providers}")
        return v.lower()

    class Config:
        extra = "forbid"


# =============================================================================
# Database Configuration
# =============================================================================

class DatabaseConfig(BaseModel):
    """Database configuration"""

    enabled: bool = Field(False, description="Enable database integration")
    database_url: str = Field("sqlite:///trading.db", description="Database URL")
    pool_size: int = Field(5, ge=1, le=20, description="Connection pool size")
    max_overflow: int = Field(10, ge=0, le=50, description="Max overflow connections")
    echo_queries: bool = Field(False, description="Echo SQL queries (debug)")

    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format"""
        valid_schemes = ['sqlite', 'postgresql', 'mysql']
        if not any(v.startswith(f'{scheme}://') or v.startswith(f'{scheme}:///')
                   for scheme in valid_schemes):
            raise ValueError(
                f"database_url must start with one of: {[f'{s}://' for s in valid_schemes]}"
            )
        return v

    class Config:
        extra = "forbid"


# =============================================================================
# Complete System Configuration
# =============================================================================

class SystemConfig(BaseModel):
    """Complete system configuration combining all sections"""

    mt5: MT5ConnectionConfig
    trading: TradingConfig
    ml: Optional[MLConfig] = None
    llm: Optional[LLMConfig] = None
    database: Optional[DatabaseConfig] = None

    class Config:
        extra = "forbid"


# =============================================================================
# Validation Helper Functions
# =============================================================================

def validate_config_file(config_dict: Dict[str, Any], config_type: str = "trading") -> BaseModel:
    """
    Validate a configuration dictionary against the appropriate schema

    Args:
        config_dict: Raw configuration dictionary (from YAML/JSON)
        config_type: Type of config ("trading", "mt5", "system", etc.)

    Returns:
        Validated Pydantic model

    Raises:
        ValidationError: If configuration is invalid
    """
    config_map = {
        "trading": TradingConfig,
        "mt5": MT5ConnectionConfig,
        "currency": CurrencyConfig,
        "ml": MLConfig,
        "llm": LLMConfig,
        "database": DatabaseConfig,
        "system": SystemConfig,
    }

    if config_type not in config_map:
        raise ValueError(f"Unknown config type: {config_type}. Valid types: {list(config_map.keys())}")

    ConfigModel = config_map[config_type]
    return ConfigModel(**config_dict)


def load_and_validate_yaml(filepath: str, config_type: str = "trading") -> BaseModel:
    """
    Load YAML file and validate against schema

    Args:
        filepath: Path to YAML configuration file
        config_type: Type of configuration

    Returns:
        Validated Pydantic model

    Raises:
        ValidationError: If configuration is invalid
        FileNotFoundError: If file doesn't exist
    """
    import yaml

    with open(filepath, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)

    return validate_config_file(config_dict, config_type)


# =============================================================================
# Example Usage & Testing
# =============================================================================

if __name__ == '__main__':
    # Example: Validate currency config
    currency_data = {
        "symbol": "EURUSD",
        "enabled": True,
        "strategy": "rsi",
        "timeframe": "H1",
        "risk_percent": 2.0,
        "max_positions": 3,
        "use_position_trading": True,
        "check_interval_seconds": 30,
        "use_fixed_sl": False,
        "atr_period": 14,
        "atr_sl_multiplier": 2.0,
        "atr_tp_multiplier": 3.0,
        "enable_breakeven": True,
        "breakeven_trigger_pips": 15.0,
        "breakeven_offset_pips": 2.0,
        "enable_trailing": True,
        "trailing_start_pips": 20.0,
        "trailing_distance_pips": 10.0,
        "enable_partial_close": False,
        "partial_close_percent": 50.0,
        "partial_close_profit_pips": 25.0
    }

    try:
        config = CurrencyConfig(**currency_data)
        print("✅ Currency config validation passed!")
        print(f"Symbol: {config.symbol}, Strategy: {config.strategy}, Risk: {config.risk_percent}%")
    except Exception as e:
        print(f"❌ Validation failed: {e}")

    # Example: Invalid config (should fail)
    print("\nTesting invalid config...")
    invalid_currency_data = {
        **currency_data,
        "risk_percent": 15.0  # Too high (max is 10.0)
    }

    try:
        config = CurrencyConfig(**invalid_currency_data)
        print("❌ Should have failed!")
    except Exception as e:
        print(f"✅ Correctly rejected invalid config: {e}")
