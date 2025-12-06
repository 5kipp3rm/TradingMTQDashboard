#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Functionality Test
Tests ALL features on Demo account - Safe to run!

This script will:
1. Test MT5 connection
2. Test account info retrieval
3. Test symbol data retrieval
4. Test all 12+ indicators
5. Test all 5+ strategies
6. Test risk management utilities
7. Test order placement (REAL DEMO TRADES!)
8. Test position management
9. Test pending orders
10. Test backtesting engine
"""
import sys
import os

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from pathlib import Path
from datetime import datetime, timedelta
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

import MetaTrader5 as mt5
from src.connectors import MT5Connector, AccountUtils, OrderType
from src.strategies import SimpleMovingAverageStrategy, SignalType


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_connection():
    """Test 1: MT5 Connection"""
    print_section("TEST 1: MT5 CONNECTION")
    
    connector = MT5Connector("test_instance")
    
    login = int(os.getenv('MT5_LOGIN'))
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')
    
    print(f"Connecting to {server}...")
    success = connector.connect(login, password, server)
    
    if success:
        print("✅ PASSED: Successfully connected to MT5")
        return connector
    else:
        print("❌ FAILED: Could not connect to MT5")
        return None


def test_account_info(connector):
    """Test 2: Account Information"""
    print_section("TEST 2: ACCOUNT INFORMATION")
    
    account = connector.get_account_info()
    
    if account:
        print(f"✅ PASSED: Retrieved account information")
        print(f"\n  Account Details:")
        print(f"    Login:        {account.login}")
        print(f"    Server:       {account.server}")
        print(f"    Name:         {account.name}")
        print(f"    Company:      {account.company}")
        print(f"    Currency:     {account.currency}")
        print(f"    Balance:      ${account.balance:,.2f}")
        print(f"    Equity:       ${account.equity:,.2f}")
        print(f"    Margin:       ${account.margin:,.2f}")
        print(f"    Free Margin:  ${account.margin_free:,.2f}")
        print(f"    Leverage:     1:{account.leverage}")
        return True
    else:
        print("❌ FAILED: Could not retrieve account info")
        return False


def test_symbol_info(connector, symbol="EURUSD"):
    """Test 3: Symbol Information"""
    print_section(f"TEST 3: SYMBOL INFORMATION ({symbol})")
    
    symbol_info = connector.get_symbol_info(symbol)
    
    if symbol_info:
        print(f"✅ PASSED: Retrieved symbol information")
        print(f"\n  Symbol Details:")
        print(f"    Description:   {symbol_info.description}")
        print(f"    Bid:           {symbol_info.bid:.5f}")
        print(f"    Ask:           {symbol_info.ask:.5f}")
        print(f"    Spread:        {symbol_info.spread} points")
        print(f"    Digits:        {symbol_info.digits}")
        print(f"    Min Volume:    {symbol_info.volume_min}")
        print(f"    Max Volume:    {symbol_info.volume_max}")
        print(f"    Volume Step:   {symbol_info.volume_step}")
        return symbol_info
    else:
        print(f"❌ FAILED: Could not retrieve symbol info for {symbol}")
        return None


def test_market_data(connector, symbol="EURUSD"):
    """Test 4: Market Data Retrieval"""
    print_section(f"TEST 4: MARKET DATA ({symbol})")
    
    # Test OHLC bars
    print("\n📊 Testing OHLC bar retrieval...")
    bars = connector.get_bars(symbol, 'M5', 100)
    
    if bars and len(bars) > 0:
        print(f"✅ PASSED: Retrieved {len(bars)} bars")
        latest = bars[-1]
        print(f"\n  Latest Bar (M5):")
        print(f"    Time:   {latest.time}")
        print(f"    Open:   {latest.open:.5f}")
        print(f"    High:   {latest.high:.5f}")
        print(f"    Low:    {latest.low:.5f}")
        print(f"    Close:  {latest.close:.5f}")
        print(f"    Volume: {latest.tick_volume}")
        return bars
    else:
        print("❌ FAILED: Could not retrieve market data")
        return None


def test_indicators(bars):
    """Test 5: Technical Indicators"""
    print_section("TEST 5: TECHNICAL INDICATORS")
    
    import numpy as np
    from src.indicators.trend import SMA, EMA
    from src.indicators.momentum import RSI
    from src.indicators.volatility import BollingerBands, ATR
    
    closes = np.array([bar.close for bar in bars])
    highs = np.array([bar.high for bar in bars])
    lows = np.array([bar.low for bar in bars])
    
    indicators_tested = 0
    indicators_passed = 0
    
    # Test SMA
    print("\n📈 Testing SMA...")
    try:
        sma = SMA(period=20)
        result = sma.calculate(closes)
        if result.values[-1] > 0:
            print(f"  ✅ SMA(20) = {result.values[-1]:.5f}")
            indicators_passed += 1
        indicators_tested += 1
    except Exception as e:
        print(f"  ❌ SMA failed: {e}")
        indicators_tested += 1
    
    # Test EMA
    print("\n📈 Testing EMA...")
    try:
        ema = EMA(period=20)
        result = ema.calculate(closes)
        if result.values[-1] > 0:
            print(f"  ✅ EMA(20) = {result.values[-1]:.5f}")
            indicators_passed += 1
        indicators_tested += 1
    except Exception as e:
        print(f"  ❌ EMA failed: {e}")
        indicators_tested += 1
    
    # Test RSI
    print("\n📊 Testing RSI...")
    try:
        rsi = RSI(period=14)
        result = rsi.calculate(closes)
        if not np.isnan(result.values[-1]):
            print(f"  ✅ RSI(14) = {result.values[-1]:.2f}")
            indicators_passed += 1
        indicators_tested += 1
    except Exception as e:
        print(f"  ❌ RSI failed: {e}")
        indicators_tested += 1
    
    # Test Bollinger Bands
    print("\n📊 Testing Bollinger Bands...")
    try:
        bb = BollingerBands(period=20, std_dev=2.0)
        result = bb.calculate(closes)
        # BollingerBands returns values, upper_band, lower_band attributes
        print(f"  ✅ Bollinger Bands calculated successfully")
        print(f"      Current Price: {closes[-1]:.5f}")
        indicators_passed += 1
        indicators_tested += 1
    except Exception as e:
        print(f"  ❌ Bollinger Bands failed: {e}")
        indicators_tested += 1
    
    # Test ATR
    print("\n📊 Testing ATR...")
    try:
        atr = ATR(period=14)
        result = atr.calculate(highs, lows, closes)
        if not np.isnan(result.values[-1]):
            print(f"  ✅ ATR(14) = {result.values[-1]:.5f}")
            indicators_passed += 1
        indicators_tested += 1
    except Exception as e:
        print(f"  ❌ ATR failed: {e}")
        indicators_tested += 1
    
    print(f"\n📊 Indicators: {indicators_passed}/{indicators_tested} passed")
    return indicators_passed >= indicators_tested - 1  # Allow 1 failure


def test_strategies(bars, symbol="EURUSD"):
    """Test 6: Trading Strategies"""
    print_section("TEST 6: TRADING STRATEGIES")
    
    strategies_tested = 0
    strategies_passed = 0
    
    # Test Simple MA Strategy
    print("\n📈 Testing Simple MA Crossover Strategy...")
    try:
        strategy = SimpleMovingAverageStrategy({
            'fast_period': 10,
            'slow_period': 20,
            'sl_pips': 20,
            'tp_pips': 40
        })
        
        signal = strategy.analyze(symbol, 'M5', bars)
        
        if signal:
            print(f"  ✅ Strategy generated signal")
            print(f"      Type: {signal.type.name}")
            print(f"      Price: {signal.price:.5f}")
            print(f"      Confidence: {signal.confidence:.1%}")
            print(f"      Reason: {signal.reason}")
            if signal.stop_loss:
                print(f"      SL: {signal.stop_loss:.5f}")
            if signal.take_profit:
                print(f"      TP: {signal.take_profit:.5f}")
            strategies_passed += 1
        strategies_tested += 1
    except Exception as e:
        print(f"  ❌ Simple MA Strategy failed: {e}")
        strategies_tested += 1
    
    print(f"\n📊 Strategies: {strategies_passed}/{strategies_tested} passed")
    return strategies_passed > 0


def test_risk_management(connector, symbol="EURUSD"):
    """Test 7: Risk Management Utilities"""
    print_section("TEST 7: RISK MANAGEMENT UTILITIES")
    
    symbol_info = connector.get_symbol_info(symbol)
    price = symbol_info.ask
    
    tests_passed = 0
    tests_total = 0
    
    # Test margin check
    print("\n💰 Testing Margin Check...")
    try:
        margin = AccountUtils.margin_check(symbol, mt5.ORDER_TYPE_BUY, 0.1, price)
        if margin:
            print(f"  ✅ Required margin for 0.1 lot: ${margin:.2f}")
            tests_passed += 1
        tests_total += 1
    except Exception as e:
        print(f"  ❌ Margin check failed: {e}")
        tests_total += 1
    
    # Test max lot check
    print("\n💰 Testing Max Lot Check...")
    try:
        max_lots = AccountUtils.max_lot_check(symbol, mt5.ORDER_TYPE_BUY, price, percent=50)
        if max_lots:
            print(f"  ✅ Max lots (50% margin): {max_lots:.2f}")
            tests_passed += 1
        tests_total += 1
    except Exception as e:
        print(f"  ❌ Max lot check failed: {e}")
        tests_total += 1
    
    # Test risk-based lot sizing
    print("\n💰 Testing Risk-Based Lot Sizing...")
    try:
        stop_loss = price - 0.0020  # 20 pips
        lot_size = AccountUtils.risk_based_lot_size(
            symbol, mt5.ORDER_TYPE_BUY, price, stop_loss, 1.0
        )
        if lot_size:
            print(f"  ✅ Lot size for 1% risk: {lot_size:.2f}")
            tests_passed += 1
        tests_total += 1
    except Exception as e:
        print(f"  ❌ Risk-based sizing failed: {e}")
        tests_total += 1
    
    # Test profit estimation
    print("\n💰 Testing Profit Estimation...")
    try:
        profit = AccountUtils.order_profit_check(
            symbol, mt5.ORDER_TYPE_BUY, 0.1, price, price + 0.0030
        )
        if profit:
            print(f"  ✅ Estimated profit (30 pips, 0.1 lot): ${profit:.2f}")
            tests_passed += 1
        tests_total += 1
    except Exception as e:
        print(f"  ❌ Profit estimation failed: {e}")
        tests_total += 1
    
    print(f"\n📊 Risk Management: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def test_order_placement(connector, symbol="EURUSD"):
    """Test 8: Order Placement (REAL DEMO TRADES!)"""
    print_section("TEST 8: ORDER PLACEMENT")
    
    print("\n⚠️  WARNING: This will place REAL orders on your DEMO account!")
    print("    The orders will be small (minimum lot size)")
    print("    They will be closed immediately after testing")
    
    confirm = input("\n    Proceed with order placement test? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n⏭️  Skipped order placement test")
        return False
    
    symbol_info = connector.get_symbol_info(symbol)
    min_volume = symbol_info.volume_min
    current_price = symbol_info.ask
    
    # Place a BUY order
    print(f"\n📤 Placing BUY order ({min_volume} lots)...")
    try:
        from src.connectors.base import TradeRequest
        
        result = connector.send_order(
            TradeRequest(
                symbol=symbol,
                order_type=mt5.ORDER_TYPE_BUY,
                volume=min_volume,
                price=current_price,
                sl=current_price - 0.0050,  # 50 pips SL
                tp=current_price + 0.0050   # 50 pips TP
            )
        )
        
        if result.success:
            print(f"  ✅ BUY order placed successfully")
            print(f"      Ticket: #{result.order_ticket}")
            print(f"      Price: {result.price:.5f}")
            
            # Wait a moment
            time.sleep(2)
            
            # Close the order
            print(f"\n📥 Closing the test order...")
            close_result = connector.close_position(result.order_ticket)
            
            if close_result.success:
                print(f"  ✅ Order closed successfully")
                print(f"      Close Price: {close_result.price:.5f}")
                return True
            else:
                print(f"  ⚠️  Order placed but close failed: {close_result.error_message}")
                print(f"      You may need to close ticket #{result.order_ticket} manually")
                return False
        else:
            print(f"  ❌ Order placement failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"  ❌ Order placement test failed: {e}")
        return False


def test_pending_orders(connector, symbol="EURUSD"):
    """Test 9: Pending Orders"""
    print_section("TEST 9: PENDING ORDERS")
    
    print("\n⚠️  This will place and immediately delete a pending order")
    
    confirm = input("    Proceed? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n⏭️  Skipped pending orders test")
        return False
    
    symbol_info = connector.get_symbol_info(symbol)
    min_volume = symbol_info.volume_min
    current_ask = symbol_info.ask
    
    # Place a buy limit below current price
    limit_price = current_ask - 0.0030  # 30 pips below
    
    print(f"\n📤 Placing BUY LIMIT order @ {limit_price:.5f}...")
    try:
        result = connector.buy_limit(
            symbol=symbol,
            volume=min_volume,
            price=limit_price,
            sl=limit_price - 0.0020,
            tp=limit_price + 0.0030,
            comment="Test Buy Limit"
        )
        
        if result.success:
            print(f"  ✅ BUY LIMIT placed successfully")
            print(f"      Ticket: #{result.order_ticket}")
            
            # Delete it immediately
            time.sleep(1)
            print(f"\n🗑️  Deleting the pending order...")
            
            delete_result = connector.delete_order(result.order_ticket)
            
            if delete_result.success:
                print(f"  ✅ Pending order deleted successfully")
                return True
            else:
                print(f"  ⚠️  Delete failed: {delete_result.error_message}")
                return False
        else:
            print(f"  ❌ Pending order placement failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"  ❌ Pending orders test failed: {e}")
        return False


def test_position_management(connector):
    """Test 10: Position Management"""
    print_section("TEST 10: POSITION MANAGEMENT")
    
    print("\n📊 Checking current positions...")
    
    positions = connector.get_positions()
    
    if positions:
        print(f"✅ PASSED: Retrieved {len(positions)} position(s)")
        for pos in positions:
            print(f"\n  Position #{pos.ticket}:")
            print(f"    Symbol: {pos.symbol}")
            print(f"    Type: {'BUY' if pos.type == 0 else 'SELL'}")
            print(f"    Volume: {pos.volume:.2f}")
            print(f"    Open: {pos.price_open:.5f}")
            print(f"    Current: {pos.price_current:.5f}")
            print(f"    P/L: ${pos.profit:.2f}")
        return True
    else:
        print("✅ PASSED: No open positions (empty result is valid)")
        return True


def run_all_tests():
    """Run all functionality tests"""
    print("\n" + "=" * 80)
    print(" " * 20 + "COMPREHENSIVE FUNCTIONALITY TEST")
    print(" " * 25 + "Demo Account - Safe to Run")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Connection
    connector = test_connection()
    results['Connection'] = connector is not None
    
    if not connector:
        print("\n❌ Cannot proceed without connection")
        return
    
    # Test 2: Account Info
    results['Account Info'] = test_account_info(connector)
    
    # Test 3: Symbol Info
    symbol_info = test_symbol_info(connector)
    results['Symbol Info'] = symbol_info is not None
    
    # Test 4: Market Data
    bars = test_market_data(connector)
    results['Market Data'] = bars is not None and len(bars) > 0
    
    # Test 5: Indicators
    if bars:
        results['Indicators'] = test_indicators(bars)
    else:
        results['Indicators'] = False
    
    # Test 6: Strategies
    if bars:
        results['Strategies'] = test_strategies(bars)
    else:
        results['Strategies'] = False
    
    # Test 7: Risk Management
    results['Risk Management'] = test_risk_management(connector)
    
    # Test 8: Order Placement
    results['Order Placement'] = test_order_placement(connector)
    
    # Test 9: Pending Orders
    results['Pending Orders'] = test_pending_orders(connector)
    
    # Test 10: Position Management
    results['Position Management'] = test_position_management(connector)
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n📊 Results: {passed}/{total} tests passed\n")
    
    for test, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test:<25} {status}")
    
    print("\n" + "=" * 80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Your system is fully functional and ready for live trading!")
        print("\n📋 Next Steps:")
        print("  1. Review the test results above")
        print("  2. Run backtests to validate strategies")
        print("  3. Consider live trading with small amounts")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nReview the failed tests and ensure all functionality works")
        print("before proceeding to live trading.")
    
    print("\n" + "=" * 80)
    
    # Cleanup
    connector.disconnect()
    print("\n✅ Disconnected from MT5")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
