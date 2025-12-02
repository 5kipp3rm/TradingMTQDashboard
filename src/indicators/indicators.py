"""
Technical Indicators Implementation
All indicators return numpy arrays or tuples of arrays
"""
import numpy as np
from typing import Tuple, List
from ..connectors.base import OHLCBar


def calculate_sma(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Simple Moving Average
    
    Args:
        closes: Array of closing prices
        period: SMA period
        
    Returns:
        Array of SMA values (NaN for initial periods)
    """
    if len(closes) < period:
        return np.full(len(closes), np.nan)
    
    sma = np.full(len(closes), np.nan)
    for i in range(period - 1, len(closes)):
        sma[i] = np.mean(closes[i - period + 1:i + 1])
    
    return sma


def calculate_ema(closes: np.ndarray, period: int) -> np.ndarray:
    """
    Exponential Moving Average
    
    Args:
        closes: Array of closing prices
        period: EMA period
        
    Returns:
        Array of EMA values
    """
    if len(closes) < period:
        return np.full(len(closes), np.nan)
    
    ema = np.full(len(closes), np.nan)
    multiplier = 2 / (period + 1)
    
    # First EMA is SMA
    ema[period - 1] = np.mean(closes[:period])
    
    # Calculate remaining EMAs
    for i in range(period, len(closes)):
        ema[i] = (closes[i] - ema[i - 1]) * multiplier + ema[i - 1]
    
    return ema


def calculate_rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Relative Strength Index
    
    Args:
        closes: Array of closing prices
        period: RSI period (default 14)
        
    Returns:
        Array of RSI values (0-100)
    """
    if len(closes) < period + 1:
        return np.full(len(closes), np.nan)
    
    # Calculate price changes
    deltas = np.diff(closes)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate average gains and losses
    avg_gains = np.full(len(closes), np.nan)
    avg_losses = np.full(len(closes), np.nan)
    
    # Initial averages
    avg_gains[period] = np.mean(gains[:period])
    avg_losses[period] = np.mean(losses[:period])
    
    # Smoothed averages
    for i in range(period + 1, len(closes)):
        avg_gains[i] = (avg_gains[i - 1] * (period - 1) + gains[i - 1]) / period
        avg_losses[i] = (avg_losses[i - 1] * (period - 1) + losses[i - 1]) / period
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(closes: np.ndarray, fast: int = 12, slow: int = 26, 
                   signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    MACD (Moving Average Convergence Divergence)
    
    Args:
        closes: Array of closing prices
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
        
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    ema_fast = calculate_ema(closes, fast)
    ema_slow = calculate_ema(closes, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line[~np.isnan(macd_line)], signal)
    
    # Pad signal line to match length
    full_signal = np.full(len(closes), np.nan)
    full_signal[-len(signal_line):] = signal_line
    
    histogram = macd_line - full_signal
    
    return macd_line, full_signal, histogram


def calculate_bollinger_bands(closes: np.ndarray, period: int = 20, 
                              std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Bollinger Bands
    
    Args:
        closes: Array of closing prices
        period: SMA period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)
        
    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    middle = calculate_sma(closes, period)
    
    std = np.full(len(closes), np.nan)
    for i in range(period - 1, len(closes)):
        std[i] = np.std(closes[i - period + 1:i + 1])
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def calculate_atr(bars: List[OHLCBar], period: int = 14) -> np.ndarray:
    """
    Average True Range
    
    Args:
        bars: List of OHLC bars
        period: ATR period (default 14)
        
    Returns:
        Array of ATR values
    """
    if len(bars) < period + 1:
        return np.full(len(bars), np.nan)
    
    highs = np.array([bar.high for bar in bars])
    lows = np.array([bar.low for bar in bars])
    closes = np.array([bar.close for bar in bars])
    
    # Calculate True Range
    tr = np.full(len(bars), np.nan)
    tr[0] = highs[0] - lows[0]
    
    for i in range(1, len(bars)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)
    
    # Calculate ATR
    atr = np.full(len(bars), np.nan)
    atr[period] = np.mean(tr[1:period + 1])
    
    for i in range(period + 1, len(bars)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    
    return atr


def calculate_stochastic(bars: List[OHLCBar], k_period: int = 14, 
                        d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stochastic Oscillator
    
    Args:
        bars: List of OHLC bars
        k_period: %K period (default 14)
        d_period: %D period (default 3)
        
    Returns:
        Tuple of (%K, %D)
    """
    if len(bars) < k_period:
        return np.full(len(bars), np.nan), np.full(len(bars), np.nan)
    
    highs = np.array([bar.high for bar in bars])
    lows = np.array([bar.low for bar in bars])
    closes = np.array([bar.close for bar in bars])
    
    k = np.full(len(bars), np.nan)
    
    for i in range(k_period - 1, len(bars)):
        highest = np.max(highs[i - k_period + 1:i + 1])
        lowest = np.min(lows[i - k_period + 1:i + 1])
        
        if highest != lowest:
            k[i] = ((closes[i] - lowest) / (highest - lowest)) * 100
        else:
            k[i] = 50
    
    # %D is SMA of %K
    d = calculate_sma(k, d_period)
    
    return k, d


def calculate_adx(bars: List[OHLCBar], period: int = 14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Average Directional Index
    
    Args:
        bars: List of OHLC bars
        period: ADX period (default 14)
        
    Returns:
        Tuple of (ADX, +DI, -DI)
    """
    if len(bars) < period + 1:
        empty = np.full(len(bars), np.nan)
        return empty, empty, empty
    
    highs = np.array([bar.high for bar in bars])
    lows = np.array([bar.low for bar in bars])
    closes = np.array([bar.close for bar in bars])
    
    # Calculate +DM and -DM
    plus_dm = np.full(len(bars), 0.0)
    minus_dm = np.full(len(bars), 0.0)
    
    for i in range(1, len(bars)):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move
    
    # Calculate ATR
    atr = calculate_atr(bars, period)
    
    # Smooth +DM and -DM
    plus_di = np.full(len(bars), np.nan)
    minus_di = np.full(len(bars), np.nan)
    
    # Initial smoothed values
    smooth_plus = np.sum(plus_dm[1:period + 1])
    smooth_minus = np.sum(minus_dm[1:period + 1])
    
    for i in range(period, len(bars)):
        if i == period:
            smooth_plus = np.sum(plus_dm[1:period + 1])
            smooth_minus = np.sum(minus_dm[1:period + 1])
        else:
            smooth_plus = smooth_plus - (smooth_plus / period) + plus_dm[i]
            smooth_minus = smooth_minus - (smooth_minus / period) + minus_dm[i]
        
        if atr[i] != 0:
            plus_di[i] = (smooth_plus / atr[i]) * 100
            minus_di[i] = (smooth_minus / atr[i]) * 100
    
    # Calculate DX and ADX
    dx = np.full(len(bars), np.nan)
    for i in range(period, len(bars)):
        if plus_di[i] + minus_di[i] != 0:
            dx[i] = abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i]) * 100
    
    adx = calculate_ema(dx[~np.isnan(dx)], period)
    full_adx = np.full(len(bars), np.nan)
    full_adx[-len(adx):] = adx
    
    return full_adx, plus_di, minus_di


def calculate_cci(bars: List[OHLCBar], period: int = 20) -> np.ndarray:
    """
    Commodity Channel Index
    
    Args:
        bars: List of OHLC bars
        period: CCI period (default 20)
        
    Returns:
        Array of CCI values
    """
    if len(bars) < period:
        return np.full(len(bars), np.nan)
    
    # Typical Price
    tp = np.array([(bar.high + bar.low + bar.close) / 3 for bar in bars])
    
    cci = np.full(len(bars), np.nan)
    
    for i in range(period - 1, len(bars)):
        sma = np.mean(tp[i - period + 1:i + 1])
        mad = np.mean(np.abs(tp[i - period + 1:i + 1] - sma))
        
        if mad != 0:
            cci[i] = (tp[i] - sma) / (0.015 * mad)
    
    return cci


def calculate_williams_r(bars: List[OHLCBar], period: int = 14) -> np.ndarray:
    """
    Williams %R
    
    Args:
        bars: List of OHLC bars
        period: Williams %R period (default 14)
        
    Returns:
        Array of Williams %R values (-100 to 0)
    """
    if len(bars) < period:
        return np.full(len(bars), np.nan)
    
    highs = np.array([bar.high for bar in bars])
    lows = np.array([bar.low for bar in bars])
    closes = np.array([bar.close for bar in bars])
    
    wr = np.full(len(bars), np.nan)
    
    for i in range(period - 1, len(bars)):
        highest = np.max(highs[i - period + 1:i + 1])
        lowest = np.min(lows[i - period + 1:i + 1])
        
        if highest != lowest:
            wr[i] = ((highest - closes[i]) / (highest - lowest)) * -100
        else:
            wr[i] = -50
    
    return wr


def calculate_roc(closes: np.ndarray, period: int = 12) -> np.ndarray:
    """
    Rate of Change
    
    Args:
        closes: Array of closing prices
        period: ROC period (default 12)
        
    Returns:
        Array of ROC values (percentage)
    """
    if len(closes) < period + 1:
        return np.full(len(closes), np.nan)
    
    roc = np.full(len(closes), np.nan)
    
    for i in range(period, len(closes)):
        if closes[i - period] != 0:
            roc[i] = ((closes[i] - closes[i - period]) / closes[i - period]) * 100
    
    return roc


def calculate_obv(bars: List[OHLCBar]) -> np.ndarray:
    """
    On-Balance Volume
    
    Args:
        bars: List of OHLC bars
        
    Returns:
        Array of OBV values
    """
    closes = np.array([bar.close for bar in bars])
    volumes = np.array([bar.tick_volume for bar in bars])
    
    obv = np.zeros(len(bars))
    
    for i in range(1, len(bars)):
        if closes[i] > closes[i - 1]:
            obv[i] = obv[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv[i] = obv[i - 1] - volumes[i]
        else:
            obv[i] = obv[i - 1]
    
    return obv
