"""
Test MT5 Connection
Simple script to verify MT5 connection works
"""
import MetaTrader5 as mt5
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.connectors import MT5Connector

def main():
    print("\n" + "=" * 80)
    print("  MT5 CONNECTION TEST")
    print("=" * 80)
    
    # Get credentials
    login = input("\nMT5 Login: ").strip()
    password = input("MT5 Password: ").strip()
    server = input("MT5 Server: ").strip()
    
    # Connect
    connector = MT5Connector()
    print(f"\nConnecting to {server}...")
    
    success = connector.connect(int(login), password, server)
    
    if not success:
        print("\n✗ CONNECTION FAILED")
        print("\nTroubleshooting:")
        print("  1. Is MT5 running?")
        print("  2. Are credentials correct?")
        print("  3. Is server name exact? (case-sensitive)")
        print("  4. Is internet connected?")
        return False
    
    print("\n✓ CONNECTION SUCCESSFUL")
    
    # Get account info
    account = connector.get_account_info()
    print("\n" + "-" * 80)
    print("ACCOUNT INFORMATION")
    print("-" * 80)
    print(f"Login:          {account.login}")
    print(f"Server:         {account.server}")
    print(f"Name:           {account.name}")
    print(f"Company:        {account.company}")
    print(f"Currency:       {account.currency}")
    print(f"Balance:        ${account.balance:,.2f}")
    print(f"Equity:         ${account.equity:,.2f}")
    print(f"Margin:         ${account.margin:,.2f}")
    print(f"Free Margin:    ${account.margin_free:,.2f}")
    print(f"Margin Level:   {account.margin_level:.2f}%")
    print(f"Profit:         ${account.profit:,.2f}")
    print(f"Leverage:       1:{account.leverage}")
    
    # Test symbol
    test_symbol = input("\n\nTest symbol (e.g., EURUSD): ").strip()
    
    if test_symbol:
        symbol_info = connector.get_symbol_info(test_symbol)
        
        if symbol_info:
            print("\n" + "-" * 80)
            print(f"SYMBOL INFORMATION - {test_symbol}")
            print("-" * 80)
            print(f"Description:    {symbol_info.description}")
            print(f"Bid:            {symbol_info.bid:.5f}")
            print(f"Ask:            {symbol_info.ask:.5f}")
            print(f"Spread:         {symbol_info.spread} points")
            print(f"Digits:         {symbol_info.digits}")
            print(f"Point:          {symbol_info.point}")
            print(f"Trade Mode:     {symbol_info.trade_mode}")
            print(f"Min Volume:     {symbol_info.volume_min}")
            print(f"Max Volume:     {symbol_info.volume_max}")
            print(f"Volume Step:    {symbol_info.volume_step}")
            print(f"Contract Size:  {symbol_info.trade_contract_size}")
            
            # Test getting bars
            print(f"\nGetting last 10 bars (M5)...")
            bars = connector.get_bars(test_symbol, 'M5', 10)
            
            if bars:
                print(f"✓ Retrieved {len(bars)} bars")
                latest = bars[-1]
                print(f"\nLatest Bar:")
                print(f"  Time:   {latest.time}")
                print(f"  Open:   {latest.open:.5f}")
                print(f"  High:   {latest.high:.5f}")
                print(f"  Low:    {latest.low:.5f}")
                print(f"  Close:  {latest.close:.5f}")
                print(f"  Volume: {latest.tick_volume}")
            else:
                print("✗ Failed to get bars")
        else:
            print(f"\n✗ Symbol {test_symbol} not found or not available")
    
    # Check positions
    positions = connector.get_positions()
    
    if positions:
        print("\n" + "-" * 80)
        print(f"OPEN POSITIONS ({len(positions)})")
        print("-" * 80)
        
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            print(f"\n#{pos.ticket} - {pos.symbol}")
            print(f"  Type:      {pos_type}")
            print(f"  Volume:    {pos.volume:.2f}")
            print(f"  Open:      {pos.price_open:.5f}")
            print(f"  Current:   {pos.price_current:.5f}")
            print(f"  SL:        {pos.sl:.5f}")
            print(f"  TP:        {pos.tp:.5f}")
            print(f"  Profit:    ${pos.profit:.2f}")
            print(f"  Comment:   {pos.comment}")
    else:
        print("\n✓ No open positions")
    
    # Disconnect
    connector.disconnect()
    print("\n✓ Disconnected successfully")
    print("\n" + "=" * 80)
    print("  CONNECTION TEST COMPLETE")
    print("=" * 80)
    print("\n✓ Your MT5 connection is working correctly!")
    print("\nNext steps:")
    print("  1. Review live_trading.py and update credentials")
    print("  2. Read LIVE_TRADING_GUIDE.md for full documentation")
    print("  3. Start with demo account and low risk %")
    print("\n" + "=" * 80 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
