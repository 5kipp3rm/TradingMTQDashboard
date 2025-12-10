"""
Feature Engineering for ML Models
Transforms OHLC data into ML-ready features
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.indicators import (
    SMA, EMA, RSI, MACD, BollingerBands, ATR
)
# Note: Using indicator classes instead of calculate_* functions


@dataclass
class FeatureSet:
    """Container for engineered features"""
    features: pd.DataFrame
    feature_names: List[str]
    target: Optional[np.ndarray] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureEngineer:
    """
    Feature engineering pipeline for trading ML models
    
    Generates features from OHLC data:
    - Technical indicators
    - Price patterns
    - Volatility measures
    - Momentum features
    - Time-based features
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feature engineer
        
        Args:
            config: Feature configuration
        """
        self.config = config or self._default_config()
        self.feature_names = []
    
    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Default feature configuration"""
        return {
            'technical_indicators': True,
            'price_features': True,
            'volatility_features': True,
            'momentum_features': True,
            'time_features': False,
            
            # Indicator parameters
            'sma_periods': [10, 20, 50],
            'ema_periods': [12, 26],
            'rsi_period': 14,
            'macd_params': (12, 26, 9),
            'bb_period': 20,
            'atr_period': 14,
            'adx_period': 14,
            'stoch_params': (14, 3, 3),
        }
    
    def transform(self, bars: pd.DataFrame) -> FeatureSet:
        """
        Transform OHLC data into features
        
        Args:
            bars: DataFrame with columns: timestamp, open, high, low, close, volume
            
        Returns:
            FeatureSet with engineered features
        """
        df = bars.copy()
        features = pd.DataFrame(index=df.index)
        
        # 1. Technical Indicators
        if self.config.get('technical_indicators'):
            features = self._add_technical_indicators(df, features)
        
        # 2. Price Features
        if self.config.get('price_features'):
            features = self._add_price_features(df, features)
        
        # 3. Volatility Features
        if self.config.get('volatility_features'):
            features = self._add_volatility_features(df, features)
        
        # 4. Momentum Features
        if self.config.get('momentum_features'):
            features = self._add_momentum_features(df, features)
        
        # 5. Time Features
        if self.config.get('time_features'):
            features = self._add_time_features(df, features)
        
        # Drop NaN rows (from indicator warmup)
        features = features.dropna()
        
        self.feature_names = list(features.columns)
        
        return FeatureSet(
            features=features,
            feature_names=self.feature_names,
            metadata={'n_features': len(self.feature_names)}
        )
    
    def _add_technical_indicators(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicator features"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # Moving Averages
        for period in self.config['sma_periods']:
            sma_ind = SMA(period=period)
            sma_result = sma_ind.calculate(close)
            sma = sma_result.values if hasattr(sma_result, 'values') else sma_result
            features[f'sma_{period}'] = sma
            features[f'price_to_sma_{period}'] = close / sma  # Relative position
        
        for period in self.config['ema_periods']:
            ema_ind = EMA(period=period)
            ema_result = ema_ind.calculate(close)
            ema = ema_result.values if hasattr(ema_result, 'values') else ema_result
            features[f'ema_{period}'] = ema
            features[f'price_to_ema_{period}'] = close / ema
        
        # RSI
        rsi_ind = RSI(period=self.config['rsi_period'])
        rsi_result = rsi_ind.calculate(close)
        rsi = rsi_result.values if hasattr(rsi_result, 'values') else rsi_result
        features['rsi'] = rsi
        features['rsi_oversold'] = (rsi < 30).astype(int)
        features['rsi_overbought'] = (rsi > 70).astype(int)
        
        # MACD
        fast, slow, signal_period = self.config['macd_params']
        macd_ind = MACD(fast_period=fast, slow_period=slow, signal_period=signal_period)
        macd_result = macd_ind.calculate(close)
        # MACD returns values as main line, metadata contains signal and histogram
        features['macd'] = macd_result.values
        features['macd_signal'] = macd_result.metadata['signal_line']
        features['macd_histogram'] = macd_result.metadata['histogram']
        features['macd_cross'] = (macd_result.values > macd_result.metadata['signal_line']).astype(int)
        
        # Bollinger Bands
        bb_ind = BollingerBands(period=self.config['bb_period'])
        bb_result = bb_ind.calculate(close)
        # BB returns middle as values, upper/lower in metadata
        features['bb_middle'] = bb_result.values
        features['bb_upper'] = bb_result.metadata['upper_band']
        features['bb_lower'] = bb_result.metadata['lower_band']
        features['bb_width'] = (bb_result.metadata['upper_band'] - bb_result.metadata['lower_band']) / bb_result.values
        features['bb_position'] = (close - bb_result.metadata['lower_band']) / (bb_result.metadata['upper_band'] - bb_result.metadata['lower_band'])  # 0-1 range
        
        # ATR
        atr_ind = ATR(period=self.config['atr_period'])
        atr_result = atr_ind.calculate(close, high=high, low=low)
        atr = atr_result.values if hasattr(atr_result, 'values') else atr_result
        features['atr'] = atr
        features['atr_pct'] = atr / close  # Normalized ATR
        
        # Note: ADX and Stochastic not yet implemented in indicators module
        # Skip for now - can add when those indicators are ready
        
        return features
    
    def _add_price_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        # Returns
        features['returns_1'] = df['close'].pct_change(1)
        features['returns_5'] = df['close'].pct_change(5)
        features['returns_10'] = df['close'].pct_change(10)
        
        # Price ranges
        features['high_low_range'] = (df['high'] - df['low']) / df['close']
        features['open_close_range'] = abs(df['open'] - df['close']) / df['close']
        
        # Candle patterns
        features['bullish_candle'] = (df['close'] > df['open']).astype(int)
        features['bearish_candle'] = (df['close'] < df['open']).astype(int)
        features['doji'] = (abs(df['close'] - df['open']) / df['close'] < 0.001).astype(int)
        
        # Price momentum
        features['price_momentum_5'] = df['close'] / df['close'].shift(5) - 1
        features['price_momentum_10'] = df['close'] / df['close'].shift(10) - 1
        
        return features
    
    def _add_volatility_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """Add volatility features"""
        returns = df['close'].pct_change()
        
        # Rolling volatility
        features['volatility_10'] = returns.rolling(10).std()
        features['volatility_20'] = returns.rolling(20).std()
        
        # Rolling range
        features['range_10'] = (df['high'].rolling(10).max() - df['low'].rolling(10).min()) / df['close']
        features['range_20'] = (df['high'].rolling(20).max() - df['low'].rolling(20).min()) / df['close']
        
        return features
    
    def _add_momentum_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """Add momentum features"""
        # Rate of change
        features['roc_5'] = (df['close'] / df['close'].shift(5) - 1) * 100
        features['roc_10'] = (df['close'] / df['close'].shift(10) - 1) * 100
        
        # Moving average crossovers
        if 'sma_10' in features and 'sma_20' in features:
            features['ma_cross_10_20'] = (features['sma_10'] > features['sma_20']).astype(int)
        
        if 'ema_12' in features and 'ema_26' in features:
            features['ma_cross_12_26'] = (features['ema_12'] > features['ema_26']).astype(int)
        
        return features
    
    def _add_time_features(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features"""
        if 'timestamp' in df.columns:
            timestamps = pd.to_datetime(df['timestamp'])
            features['hour'] = timestamps.dt.hour
            features['day_of_week'] = timestamps.dt.dayofweek
            features['month'] = timestamps.dt.month
        
        return features
    
    def create_target(self, bars: pd.DataFrame, target_type: str = 'direction', 
                     lookahead: int = 1, threshold: float = 0.0) -> np.ndarray:
        """
        Create target variable for supervised learning
        
        Args:
            bars: OHLC DataFrame
            target_type: 'direction' (up/down), 'return' (continuous), 'classification' (buy/sell/hold)
            lookahead: Number of periods to look ahead
            threshold: Threshold for classification (e.g., 0.001 = 0.1%)
            
        Returns:
            Target array
        """
        close = bars['close'].values
        
        if target_type == 'direction':
            # Binary: 1 if price goes up, 0 if down
            future_returns = np.roll(close, -lookahead) / close - 1
            target = (future_returns > 0).astype(int)
        
        elif target_type == 'return':
            # Continuous: future return
            target = np.roll(close, -lookahead) / close - 1
        
        elif target_type == 'classification':
            # Multi-class: BUY (1), HOLD (0), SELL (-1)
            future_returns = np.roll(close, -lookahead) / close - 1
            target = np.zeros(len(close))
            target[future_returns > threshold] = 1  # BUY
            target[future_returns < -threshold] = -1  # SELL
        
        else:
            raise ValueError(f"Unknown target_type: {target_type}")
        
        # Remove last N rows (no future data)
        target[-lookahead:] = np.nan
        
        return target
