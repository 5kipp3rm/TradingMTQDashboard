"""
Pip Calculator - Calculate profit/loss and set SL/TP in pips
"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv()
login = int(os.getenv('MT5_LOGIN', 0))
password = os.getenv('MT5_PASSWORD', '')
server = os.getenv('MT5_SERVER', '')

def pips_to_price(symbol, current_price, pips, direction='up'):
    """
    Convert pips to price
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD')
        current_price: Current market price
        pips: Number of pips
        direction: 'up' or 'down'
    
    Returns:
        Price after moving X pips
    """
    # For most forex pairs, 1 pip = 0.0001
    # For JPY pairs, 1 pip = 0.01
    symbol_info = mt5.symbol_info(symbol)
    
    if 'JPY' in symbol:
        pip_size = 0.01
    else:
        pip_size = 0.0001
    
    if direction == 'up':
        return current_price + (pips * pip_size)
    else:
        return current_price - (pips * pip_size)


def calculate_pip_value(symbol, lot_size):
    """
    Calculate how much 1 pip is worth in USD
    
    Args:
        symbol: Trading symbol
        lot_size: Position size in lots
    
    Returns:
        Value of 1 pip in account currency (USD)
    """
    symbol_info = mt5.symbol_info(symbol)
    
    if 'JPY' in symbol:
        pip_size = 0.01
    else:
        pip_size = 0.0001
    
    # Standard lot = 100,000 units
    # Pip value = (pip size * lot size * contract size)
    pip_value = pip_size * lot_size * symbol_info.trade_contract_size
    
    # For pairs where USD is the quote currency (like EURUSD)
    # pip value is already in USD
    
    # For pairs where USD is base currency (like USDJPY)
    # need to convert
    if symbol.startswith('USD'):
        # Convert to USD by dividing by current price
        tick = mt5.symbol_info_tick(symbol)
        pip_value = pip_value / tick.bid
    
    return pip_value


def calculate_profit(symbol, lot_size, pips):
    """
    Calculate profit/loss for given pips
    
    Args:
        symbol: Trading symbol
        lot_size: Position size in lots
        pips: Number of pips (positive for profit, negative for loss)
    
    Returns:
        Profit in USD
    """
    pip_value = calculate_pip_value(symbol, lot_size)
    return pip_value * pips


def interactive_calculator():
    """Interactive pip calculator"""
    
    # Initialize MT5
    if not mt5.initialize():
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        return
    
    if not mt5.login(login, password, server):
        print(f"❌ Login failed: {mt5.last_error()}")
        mt5.shutdown()
        return
    
    print("=" * 80)
    print("  PIP CALCULATOR & PROFIT ESTIMATOR")
    print("=" * 80)
    
    while True:
        print("\n" + "-" * 80)
        
        # Get inputs
        symbol = input("\nSymbol (e.g., EURUSD) or 'quit': ").strip().upper()
        if symbol in ['QUIT', 'Q', 'EXIT']:
            break
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            print(f"❌ Symbol {symbol} not found!")
            continue
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"❌ Could not get price for {symbol}")
            continue
        
        print(f"\n{symbol} Current Prices:")
        print(f"  Bid: {tick.bid:.5f}")
        print(f"  Ask: {tick.ask:.5f}")
        print(f"  Spread: {symbol_info.spread} points ({symbol_info.spread / 10:.1f} pips)")
        
        # Get lot size
        lot_input = input(f"\nLot size (default: 0.01): ").strip() or "0.01"
        lot_size = float(lot_input)
        
        # Calculate pip value
        pip_value = calculate_pip_value(symbol, lot_size)
        
        print(f"\n📊 For {lot_size} lot(s) of {symbol}:")
        print(f"   1 pip = ${pip_value:.2f}")
        print(f"   10 pips = ${pip_value * 10:.2f}")
        print(f"   50 pips = ${pip_value * 50:.2f}")
        print(f"   100 pips = ${pip_value * 100:.2f}")
        
        # Calculate custom profit
        print("\n" + "=" * 80)
        print("  PROFIT/LOSS CALCULATOR")
        print("=" * 80)
        
        pips_input = input("\nHow many pips profit/loss? (e.g., 30 or -20): ").strip()
        if pips_input:
            pips = float(pips_input)
            profit = calculate_profit(symbol, lot_size, pips)
            
            if pips > 0:
                print(f"\n✅ Profit for +{pips} pips: ${profit:.2f}")
            else:
                print(f"\n❌ Loss for {pips} pips: ${profit:.2f}")
        
        # Calculate SL/TP prices
        print("\n" + "=" * 80)
        print("  STOP LOSS / TAKE PROFIT CALCULATOR")
        print("=" * 80)
        
        order_type = input("\nOrder type (BUY or SELL): ").strip().upper()
        if order_type in ['BUY', 'SELL']:
            entry_price = tick.ask if order_type == 'BUY' else tick.bid
            
            print(f"\nEntry Price: {entry_price:.5f}")
            
            sl_pips_input = input("Stop Loss in pips (e.g., 20): ").strip()
            tp_pips_input = input("Take Profit in pips (e.g., 40): ").strip()
            
            if sl_pips_input:
                sl_pips = float(sl_pips_input)
                if order_type == 'BUY':
                    sl_price = pips_to_price(symbol, entry_price, sl_pips, 'down')
                else:
                    sl_price = pips_to_price(symbol, entry_price, sl_pips, 'up')
                
                sl_loss = calculate_profit(symbol, lot_size, -sl_pips)
                print(f"\n🛑 Stop Loss:")
                print(f"   Pips: {sl_pips}")
                print(f"   Price: {sl_price:.5f}")
                print(f"   Max Loss: ${abs(sl_loss):.2f}")
            
            if tp_pips_input:
                tp_pips = float(tp_pips_input)
                if order_type == 'BUY':
                    tp_price = pips_to_price(symbol, entry_price, tp_pips, 'up')
                else:
                    tp_price = pips_to_price(symbol, entry_price, tp_pips, 'down')
                
                tp_profit = calculate_profit(symbol, lot_size, tp_pips)
                print(f"\n🎯 Take Profit:")
                print(f"   Pips: {tp_pips}")
                print(f"   Price: {tp_price:.5f}")
                print(f"   Profit: ${tp_profit:.2f}")
            
            if sl_pips_input and tp_pips_input:
                risk_reward = tp_pips / sl_pips
                print(f"\n⚖️  Risk/Reward Ratio: 1:{risk_reward:.2f}")
        
        print("\n" + "-" * 80)
        another = input("\nCalculate another? (yes/no): ").strip().lower()
        if another not in ['yes', 'y', '']:
            break
    
    mt5.shutdown()
    print("\n✓ Calculator closed")


def quick_reference():
    """Print quick reference guide"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         PIP CONTROL QUICK REFERENCE                        ║
╚════════════════════════════════════════════════════════════════════════════╝

📏 WHAT IS A PIP?
   • Pip = "Point in Percentage" (smallest price movement)
   • For most pairs (EUR/USD, GBP/USD): 1 pip = 0.0001
   • For JPY pairs (USD/JPY): 1 pip = 0.01
   • Example: EUR/USD moves from 1.1000 to 1.1001 = 1 pip

💰 PIP VALUE (how much 1 pip is worth)
   Formula: Pip Size × Lot Size × Contract Size
   
   Standard Lot (1.0): 1 pip ≈ $10
   Mini Lot (0.1):     1 pip ≈ $1
   Micro Lot (0.01):   1 pip ≈ $0.10

📊 PROFIT/LOSS CALCULATION
   Profit/Loss = Pips × Pip Value × Lot Size
   
   Example: 0.1 lot EUR/USD, +30 pips
   → 30 × $1 × 1 = $30 profit

🛑 SETTING STOP LOSS (SL)
   BUY order:  SL = Entry Price - (Pips × Pip Size)
   SELL order: SL = Entry Price + (Pips × Pip Size)
   
   Example BUY EUR/USD @ 1.1000, 20 pip SL:
   → SL = 1.1000 - 0.0020 = 1.0980

🎯 SETTING TAKE PROFIT (TP)
   BUY order:  TP = Entry Price + (Pips × Pip Size)
   SELL order: TP = Entry Price - (Pips × Pip Size)
   
   Example BUY EUR/USD @ 1.1000, 40 pip TP:
   → TP = 1.1000 + 0.0040 = 1.1040

⚖️  RISK/REWARD RATIO
   RR = Take Profit Pips / Stop Loss Pips
   
   Common ratios:
   • 1:1 (20 pip SL, 20 pip TP)
   • 1:2 (20 pip SL, 40 pip TP) ← Recommended
   • 1:3 (20 pip SL, 60 pip TP)

🔧 IN CODE (Python with MT5):

   # Calculate SL/TP for BUY order
   entry_price = 1.1000
   sl_pips = 20
   tp_pips = 40
   
   sl_price = entry_price - (sl_pips * 0.0001)  # 1.0980
   tp_price = entry_price + (tp_pips * 0.0001)  # 1.1040
   
   # For SELL order, reverse the +/-
   sl_price = entry_price + (sl_pips * 0.0001)
   tp_price = entry_price - (tp_pips * 0.0001)

💡 TIPS:
   • Smaller lots = less risk per pip
   • Start with 0.01 lots while learning
   • Good SL range: 15-30 pips for scalping, 50-100 for swing trading
   • Always use SL to limit losses!
   • TP should be at least 1.5x your SL (1:1.5 ratio minimum)

╚════════════════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        quick_reference()
    else:
        quick_reference()
        print("\nStarting interactive calculator...\n")
        interactive_calculator()
