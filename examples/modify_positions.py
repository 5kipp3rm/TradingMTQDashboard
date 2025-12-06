"""
Example: Modify SL/TP on Existing Positions
Shows how to use TradingController to change stops on open trades
"""
import os
from dotenv import load_dotenv

from src.connectors import ConnectorFactory
from src.connectors.base import PlatformType
from src.trading import TradingController

load_dotenv()


def main():
    """Modify SL/TP on existing positions"""
    
    print("=" * 80)
    print("  MODIFY EXISTING POSITIONS - SL/TP MANAGER")
    print("=" * 80)
    
    # Connect
    print("\n🔌 Connecting to MT5...")
    connector = ConnectorFactory.create_connector(
        platform=PlatformType.MT5,
        instance_id="modify_bot"
    )
    
    login = int(os.getenv('MT5_LOGIN', 0))
    password = os.getenv('MT5_PASSWORD', '')
    server = os.getenv('MT5_SERVER', '')
    
    if not connector.connect(login, password, server):
        print("❌ Connection failed")
        return
    
    print("✓ Connected")
    
    # Create controller
    controller = TradingController(connector)
    
    # Get all open positions
    print("\n📊 Fetching open positions...")
    positions = controller.get_open_positions()
    
    if not positions:
        print("No open positions found")
        connector.disconnect()
        return
    
    print(f"\nFound {len(positions)} open position(s):")
    print("-" * 80)
    
    for pos in positions:
        print(f"\n{pos.symbol} - Ticket #{pos.ticket}")
        print(f"  Type: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"  Volume: {pos.volume:.2f} lots")
        print(f"  Entry: {pos.price_open:.5f}")
        print(f"  Current: {pos.price_current:.5f}")
        print(f"  SL: {pos.sl:.5f}" if pos.sl else "  SL: Not set")
        print(f"  TP: {pos.tp:.5f}" if pos.tp else "  TP: Not set")
        print(f"  Profit: ${pos.profit:.2f}")
    
    print("\n" + "=" * 80)
    print("MODIFICATION OPTIONS")
    print("=" * 80)
    
    print("\n1. Modify specific position")
    print("2. Widen all stops by X pips")
    print("3. Tighten all stops by X pips")
    print("4. Set breakeven for profitable positions")
    print("5. Remove all SL/TP")
    print("6. Exit")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    if choice == "1":
        # Modify specific position
        ticket = int(input("Enter position ticket: "))
        position = connector.get_position_by_ticket(ticket)
        
        if not position:
            print(f"❌ Position {ticket} not found")
        else:
            print(f"\nCurrent - SL: {position.sl:.5f}, TP: {position.tp:.5f}")
            
            new_sl = float(input("New SL (or 0 to remove): "))
            new_tp = float(input("New TP (or 0 to remove): "))
            
            result = controller.modify_trade(
                ticket=ticket,
                sl=new_sl if new_sl > 0 else None,
                tp=new_tp if new_tp > 0 else None
            )
            
            if result.success:
                print(f"✓ Position {ticket} modified successfully")
            else:
                print(f"✗ Failed: {result.error_message}")
    
    elif choice == "2":
        # Widen stops
        pips = int(input("Widen by how many pips? "))
        pip_value = 0.0001  # For most pairs
        
        for pos in positions:
            symbol_info = connector.get_symbol_info(pos.symbol)
            if symbol_info:
                pip_value = symbol_info.point * 10
            
            if pos.type == 0:  # BUY
                new_sl = pos.sl - (pips * pip_value) if pos.sl else None
                new_tp = pos.tp + (pips * pip_value) if pos.tp else None
            else:  # SELL
                new_sl = pos.sl + (pips * pip_value) if pos.sl else None
                new_tp = pos.tp - (pips * pip_value) if pos.tp else None
            
            result = controller.modify_trade(pos.ticket, new_sl, new_tp)
            
            if result.success:
                print(f"✓ {pos.symbol} #{pos.ticket} - Widened by {pips} pips")
            else:
                print(f"✗ {pos.symbol} #{pos.ticket} - Failed: {result.error_message}")
    
    elif choice == "3":
        # Tighten stops
        pips = int(input("Tighten by how many pips? "))
        pip_value = 0.0001
        
        for pos in positions:
            symbol_info = connector.get_symbol_info(pos.symbol)
            if symbol_info:
                pip_value = symbol_info.point * 10
            
            if pos.type == 0:  # BUY
                new_sl = pos.sl + (pips * pip_value) if pos.sl else None
                new_tp = pos.tp - (pips * pip_value) if pos.tp else None
            else:  # SELL
                new_sl = pos.sl - (pips * pip_value) if pos.sl else None
                new_tp = pos.tp + (pips * pip_value) if pos.tp else None
            
            result = controller.modify_trade(pos.ticket, new_sl, new_tp)
            
            if result.success:
                print(f"✓ {pos.symbol} #{pos.ticket} - Tightened by {pips} pips")
            else:
                print(f"✗ {pos.symbol} #{pos.ticket} - Failed: {result.error_message}")
    
    elif choice == "4":
        # Breakeven for profitable
        offset_pips = int(input("Breakeven offset in pips (e.g., 2): "))
        pip_value = 0.0001
        
        for pos in positions:
            if pos.profit <= 0:
                print(f"⏭️  {pos.symbol} #{pos.ticket} - Not profitable, skipping")
                continue
            
            symbol_info = connector.get_symbol_info(pos.symbol)
            if symbol_info:
                pip_value = symbol_info.point * 10
            
            if pos.type == 0:  # BUY
                new_sl = pos.price_open + (offset_pips * pip_value)
            else:  # SELL
                new_sl = pos.price_open - (offset_pips * pip_value)
            
            result = controller.modify_trade(pos.ticket, new_sl, pos.tp)
            
            if result.success:
                print(f"✓ {pos.symbol} #{pos.ticket} - Moved to breakeven +{offset_pips}")
            else:
                print(f"✗ {pos.symbol} #{pos.ticket} - Failed: {result.error_message}")
    
    elif choice == "5":
        # Remove all SL/TP
        confirm = input("⚠️  Remove all SL/TP? This is risky! (yes/no): ")
        if confirm.lower() == 'yes':
            for pos in positions:
                result = controller.modify_trade(pos.ticket, None, None)
                
                if result.success:
                    print(f"✓ {pos.symbol} #{pos.ticket} - SL/TP removed")
                else:
                    print(f"✗ {pos.symbol} #{pos.ticket} - Failed: {result.error_message}")
    
    elif choice == "6":
        print("Exiting...")
    
    else:
        print("Invalid choice")
    
    # Disconnect
    connector.disconnect()
    print("\n✓ Disconnected")


if __name__ == '__main__':
    main()
