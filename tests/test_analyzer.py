"""
Tests for Market Analyzer
"""
import pytest
import numpy as np
from datetime import datetime, timedelta

from src.analysis import MarketAnalyzer, MarketProfile
from src.connectors.base import OHLCBar


class TestMarketAnalyzer:
    """Test suite for MarketAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return MarketAnalyzer(lookback_hours=24)
    
    def create_test_bars(self, count=100, volatility='normal'):
        """Helper to create test bars"""
        bars = []
        base_time = datetime.now()
        base_price = 1.08500
        
        for i in range(count):
            if volatility == 'normal':
                # Normal price movement (0.1% - 5% volatility range)
                # Use larger amplitude to get ~0.2-0.3% volatility
                price = base_price + np.sin(i / 10) * 0.00200  # 20 pips amplitude
            elif volatility == 'high':
                # High volatility (>5% threshold) - need large stddev
                price = base_price + np.random.randn() * 0.06000  # 6% std dev
            elif volatility == 'low':
                # Very low volatility (<0.1% threshold)
                price = base_price + np.random.randn() * 0.00001
            else:
                price = base_price
            
            bars.append(OHLCBar(
                symbol="EURUSD",
                timeframe="H1",
                time=base_time + timedelta(hours=i),
                open=price,
                high=price + 0.00020,
                low=price - 0.00020,
                close=price,
                tick_volume=1000 + int(np.random.randn() * 100),
                real_volume=100000,
                spread=2
            ))
        
        return bars
    
    def test_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer.lookback_hours == 24
        assert len(analyzer.profiles) == 0
    
    def test_analyze_normal_market(self, analyzer):
        """Test analysis of normal market conditions"""
        # Create enough bars (>50) to avoid CAUTION from insufficient data
        bars = self.create_test_bars(100, volatility='normal')
        
        profile = analyzer.analyze_symbol("EURUSD", bars)
        
        assert profile.symbol == "EURUSD"
        # Normal volatility (sin wave ~0.03%) with low anomaly should give TRADE
        assert profile.avg_volatility < 5
        assert profile.anomaly_score < 20  # Normal market
        # With 100 bars, normal volatility, and low anomaly, should be TRADE
        assert profile.recommendation == 'TRADE'
    
    def test_analyze_high_volatility(self, analyzer):
        """Test analysis of high volatility market"""
        bars = self.create_test_bars(100, volatility='high')
        
        profile = analyzer.analyze_symbol("EURUSD", bars)
        
        assert profile.symbol == "EURUSD"
        # High volatility (random walk with 1% std) should trigger CAUTION (>5% volatility)
        assert profile.recommendation == 'CAUTION'
        assert profile.avg_volatility > 5
    
    def test_analyze_low_volatility(self, analyzer):
        """Test analysis of very low volatility market"""
        bars = self.create_test_bars(100, volatility='low')
        
        profile = analyzer.analyze_symbol("EURUSD", bars)
        
        assert profile.symbol == "EURUSD"
        # Very low volatility should trigger caution
        assert profile.recommendation == 'CAUTION'
    
    def test_insufficient_data(self, analyzer):
        """Test with insufficient data"""
        bars = self.create_test_bars(5)  # Too few bars
        
        profile = analyzer.analyze_symbol("EURUSD", bars)
        
        assert profile.symbol == "EURUSD"
        assert profile.recommendation == 'AVOID'
    
    def test_trend_detection(self, analyzer):
        """Test trend detection"""
        bars = []
        base_time = datetime.now()
        base_price = 1.08500
        
        # Create clear uptrend
        for i in range(100):
            price = base_price + i * 0.00010  # Consistent uptrend
            bars.append(OHLCBar(
                symbol="EURUSD",
                timeframe="H1",
                time=base_time + timedelta(hours=i),
                open=price,
                high=price + 0.00010,
                low=price - 0.00010,
                close=price,
                tick_volume=1000,
                real_volume=100000,
                spread=2
            ))
        
        profile = analyzer.analyze_symbol("EURUSD", bars)
        
        # numpy bool_ needs explicit bool() conversion
        assert bool(profile.is_trending) is True
        assert profile.trend_strength > 30  # Strong trend
    
    def test_anomaly_detection(self, analyzer):
        """Test anomaly detection"""
        bars = []
        base_time = datetime.now()
        base_price = 1.08500
        
        # Create normal data with anomalies
        for i in range(100):
            if i == 50:
                # Inject price spike (anomaly)
                price = base_price + 0.05000  # 500 pips spike!
            else:
                price = base_price + np.random.randn() * 0.00020
            
            bars.append(OHLCBar(
                symbol="EURUSD",
                timeframe="H1",
                time=base_time + timedelta(hours=i),
                open=price,
                high=price + 0.00010,
                low=price - 0.00010,
                close=price,
                tick_volume=1000,
                real_volume=100000,
                spread=2
            ))
        
        profile = analyzer.analyze_symbol("EURUSD", bars)
        
        # Should detect anomaly
        assert profile.anomaly_score > 0
    
    def test_should_trade_symbol(self, analyzer):
        """Test trade suitability check"""
        bars = self.create_test_bars(100, volatility='normal')
        
        analyzer.analyze_symbol("EURUSD", bars)
        
        should_trade = analyzer.should_trade_symbol("EURUSD")
        assert should_trade is True
        
        # Unknown symbol
        should_trade = analyzer.should_trade_symbol("UNKNOWN")
        assert should_trade is False
    
    def test_get_profile(self, analyzer):
        """Test profile retrieval"""
        bars = self.create_test_bars(100)
        
        analyzer.analyze_symbol("EURUSD", bars)
        
        profile = analyzer.get_profile("EURUSD")
        assert profile is not None
        assert profile.symbol == "EURUSD"
        
        # Unknown symbol
        profile = analyzer.get_profile("UNKNOWN")
        assert profile is None
    
    def test_multiple_symbols(self, analyzer):
        """Test analyzing multiple symbols"""
        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        
        for symbol in symbols:
            bars = self.create_test_bars(100)
            # Update symbol in bars
            for bar in bars:
                bar.symbol = symbol
            analyzer.analyze_symbol(symbol, bars)
        
        assert len(analyzer.profiles) == 3
        assert "EURUSD" in analyzer.profiles
        assert "GBPUSD" in analyzer.profiles
        assert "USDJPY" in analyzer.profiles
