"""
Market Analyzer - Pre-trading analysis and anomaly detection
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..connectors.base import OHLCBar
from ..utils import get_logger

logger = get_logger(__name__)


@dataclass
class MarketProfile:
    """Market profile for a symbol"""
    symbol: str
    avg_volatility: float
    avg_range: float
    avg_volume: float
    typical_spread: float
    price_mean: float
    price_std: float
    is_trending: bool
    trend_strength: float
    anomaly_score: float
    recommendation: str  # 'TRADE', 'CAUTION', 'AVOID'


class MarketAnalyzer:
    """
    Analyzes historical market data to detect:
    - Normal vs abnormal market behavior
    - Volatility patterns
    - Trend characteristics
    - Trading suitability
    """
    
    def __init__(self, lookback_hours: int = 24):
        """
        Initialize analyzer
        
        Args:
            lookback_hours: Hours of historical data to analyze
        """
        self.lookback_hours = lookback_hours
        self.profiles: Dict[str, MarketProfile] = {}
    
    def analyze_symbol(self, symbol: str, bars: List[OHLCBar]) -> MarketProfile:
        """
        Analyze a symbol's historical behavior
        
        Args:
            symbol: Trading symbol
            bars: Historical OHLC bars
            
        Returns:
            MarketProfile with analysis results
        """
        logger.info(f"Analyzing {symbol} with {len(bars)} bars ({self.lookback_hours}h history)")
        
        if len(bars) < 20:
            return self._create_default_profile(symbol, "Insufficient data")
        
        # Extract data
        closes = np.array([bar.close for bar in bars])
        highs = np.array([bar.high for bar in bars])
        lows = np.array([bar.low for bar in bars])
        volumes = np.array([bar.tick_volume for bar in bars])
        
        # Calculate volatility (ATR - Average True Range)
        ranges = highs - lows
        avg_range = np.mean(ranges)
        volatility = np.std(closes) / np.mean(closes) * 100  # CV as percentage
        
        # Calculate price statistics
        price_mean = np.mean(closes)
        price_std = np.std(closes)
        
        # Detect trend
        is_trending, trend_strength = self._detect_trend(closes)
        
        # Calculate volume stats
        avg_volume = np.mean(volumes)
        
        # Detect anomalies
        anomaly_score = self._detect_anomalies(closes, ranges, volumes)
        
        # Determine recommendation
        recommendation = self._get_recommendation(volatility, anomaly_score, len(bars))
        
        profile = MarketProfile(
            symbol=symbol,
            avg_volatility=volatility,
            avg_range=avg_range,
            avg_volume=avg_volume,
            typical_spread=avg_range / price_mean * 10000,  # In pips
            price_mean=price_mean,
            price_std=price_std,
            is_trending=is_trending,
            trend_strength=trend_strength,
            anomaly_score=anomaly_score,
            recommendation=recommendation
        )
        
        self.profiles[symbol] = profile
        return profile
    
    def _detect_trend(self, closes: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if market is trending
        
        Returns:
            (is_trending, strength) where strength is 0-100
        """
        # Simple linear regression slope
        x = np.arange(len(closes))
        coeffs = np.polyfit(x, closes, 1)
        slope = coeffs[0]
        
        # Normalize slope relative to price
        slope_normalized = abs(slope) / np.mean(closes) * 100
        
        # R-squared for trend strength
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((closes - y_pred) ** 2)
        ss_tot = np.sum((closes - np.mean(closes)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        trend_strength = r_squared * 100
        is_trending = trend_strength > 30  # More than 30% explained by trend
        
        return is_trending, trend_strength
    
    def _detect_anomalies(self, closes: np.ndarray, ranges: np.ndarray, 
                         volumes: np.ndarray) -> float:
        """
        Detect abnormal market behavior
        
        Returns:
            Anomaly score 0-100 (higher = more abnormal)
        """
        anomalies = []
        
        # Price anomalies (using Z-score)
        if len(closes) > 10:
            z_scores = np.abs((closes - np.mean(closes)) / np.std(closes))
            price_anomalies = np.sum(z_scores > 3) / len(closes)  # % outside 3 std
            anomalies.append(price_anomalies)
        
        # Range anomalies (sudden volatility spikes)
        if len(ranges) > 10:
            range_mean = np.mean(ranges)
            range_std = np.std(ranges)
            range_anomalies = np.sum(ranges > (range_mean + 3 * range_std)) / len(ranges)
            anomalies.append(range_anomalies)
        
        # Volume anomalies
        if len(volumes) > 10 and np.mean(volumes) > 0:
            vol_mean = np.mean(volumes)
            vol_std = np.std(volumes)
            vol_anomalies = np.sum(volumes > (vol_mean + 3 * vol_std)) / len(volumes)
            anomalies.append(vol_anomalies)
        
        # Average anomaly score
        avg_anomaly = np.mean(anomalies) * 100 if anomalies else 0
        
        return min(avg_anomaly, 100)
    
    def _get_recommendation(self, volatility: float, anomaly_score: float, 
                           data_points: int) -> str:
        """
        Get trading recommendation based on analysis
        
        Returns:
            'TRADE', 'CAUTION', or 'AVOID'
        """
        # Insufficient data
        if data_points < 50:
            return 'CAUTION'
        
        # High anomaly = avoid
        if anomaly_score > 20:
            return 'AVOID'
        
        # Extreme volatility = caution
        if volatility > 5.0:  # More than 5% volatility
            return 'CAUTION'
        
        # Very low volatility = caution (might be illiquid)
        if volatility < 0.1:
            return 'CAUTION'
        
        # Normal conditions = trade
        return 'TRADE'
    
    def _create_default_profile(self, symbol: str, reason: str) -> MarketProfile:
        """Create default profile when analysis fails"""
        return MarketProfile(
            symbol=symbol,
            avg_volatility=0.0,
            avg_range=0.0,
            avg_volume=0.0,
            typical_spread=0.0,
            price_mean=0.0,
            price_std=0.0,
            is_trending=False,
            trend_strength=0.0,
            anomaly_score=100.0,
            recommendation='AVOID'
        )
    
    def get_profile(self, symbol: str) -> Optional[MarketProfile]:
        """Get analyzed profile for a symbol"""
        return self.profiles.get(symbol)
    
    def should_trade_symbol(self, symbol: str) -> bool:
        """Check if symbol is suitable for trading"""
        profile = self.profiles.get(symbol)
        if not profile:
            return False
        return profile.recommendation == 'TRADE'
    
    def print_analysis_report(self):
        """Print comprehensive analysis report"""
        print("\n" + "=" * 70)
        print(" " * 20 + "📊 MARKET ANALYSIS REPORT")
        print("=" * 70)
        
        if not self.profiles:
            print("\nNo symbols analyzed yet.")
            return
        
        for symbol, profile in self.profiles.items():
            # Recommendation color
            rec_color = {
                'TRADE': '\033[32m',    # Green
                'CAUTION': '\033[33m',  # Yellow
                'AVOID': '\033[31m'     # Red
            }.get(profile.recommendation, '')
            
            print(f"\n📈 {symbol}")
            print(f"   Price: {profile.price_mean:.5f} ± {profile.price_std:.5f}")
            print(f"   Volatility: {profile.avg_volatility:.2f}% | Range: {profile.avg_range:.5f}")
            print(f"   Spread: {profile.typical_spread:.1f} pips")
            
            trend_icon = "📈" if profile.is_trending else "↔️"
            print(f"   Trend: {trend_icon} {'Yes' if profile.is_trending else 'No'} "
                  f"(Strength: {profile.trend_strength:.1f}%)")
            
            print(f"   Anomaly Score: {profile.anomaly_score:.1f}%")
            print(f"   {rec_color}► Recommendation: {profile.recommendation}\033[0m")
        
        # Summary
        trade_count = sum(1 for p in self.profiles.values() if p.recommendation == 'TRADE')
        caution_count = sum(1 for p in self.profiles.values() if p.recommendation == 'CAUTION')
        avoid_count = sum(1 for p in self.profiles.values() if p.recommendation == 'AVOID')
        
        print("\n" + "-" * 70)
        print(f"Summary: {trade_count} tradeable, {caution_count} caution, {avoid_count} avoid")
        print("=" * 70 + "\n")
