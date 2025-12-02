"""
Position Management Script
Quickly view and close positions
"""
import MetaTrader5 as mt5
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.connectors import MT5Connector, trade_server_return_code_description

# UPDATE THESE
MT5_LOGIN = 12345678
MT5_PASSWORD = "your_password"
MT5_SERVER = "YourBroker-Demo"


def show_positions(connector: MT5Connector):
    """Show all open positions"""
    positions = connector.get_positions()
    
    if not positions:
        print("\nNo open positions")
        return []
    
    print(f"\nOpen Positions ({len(positions)}):")
    print("=" * 100)
    print(f"{'#':<4} {'Ticket':<12} {'Symbol':<10} {'Type':<6} {'Volume':<8} {'Open':<10} {'Current':<10} {'P/L':<12}")
    print("-" * 100)
    
    total_profit = 0.0
    for i, pos in enumerate(positions, 1):
        pos_type = "BUY" if pos.type == 0 else "SELL"
        current = pos.price_current
        print(f"{i:<4} {pos.ticket:<12} {pos.symbol:<10} {pos_type:<6} {pos.volume:<8.2f} "
              f"{pos.price_open:<10.5f} {current:<10.5f} ${pos.profit:<12.2f}")
        total_profit += pos.profit
    
    print("-" * 100)
    print(f"{'Total P/L:':<80} ${total_profit:.2f}")
    print("=" * 100)
    
    return positions


def close_position(connector: MT5Connector, ticket: int):
    """Close a position by ticket"""
    result = connector.close_position(ticket)
    
    if result.success:
        print(f"✓ Position #{ticket} closed")
        print(f"  Close Price: {result.price:.5f}")
    else:
        error_msg = trade_server_return_code_description(result.error_code)
        print(f"✗ Failed to close position #{ticket}")
        print(f"  Error: {error_msg}")


def close_all_positions(connector: MT5Connector):
    """Close all open positions"""
    positions = connector.get_positions()
    
    if not positions:
        print("\nNo positions to close")
        return
    
    print(f"\nClosing {len(positions)} position(s)...")
    
    for pos in positions:
        close_position(connector, pos.ticket)
    
    print("\n✓ All positions closed")


def main():
    """Main entry point"""
    print("\n" + "=" * 100)
    print("  POSITION MANAGER")
    print("=" * 100)
    
    # Connect
    connector = MT5Connector("position_manager")
    
    if not connector.connect(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER):
        print("✗ Failed to connect to MT5")
        return
    
    print("✓ Connected to MT5")
    
    try:
        while True:
            # Show account
            account = connector.get_account_info()
            if account:
                print(f"\nAccount: {account.login} | Balance: ${account.balance:.2f} | "
                      f"Equity: ${account.equity:.2f} | Profit: ${account.profit:.2f}")
            
            # Show positions
            positions = show_positions(connector)
            
            if not positions:
                break
            
            # Menu
            print("\nOptions:")
            print("  1-{}: Close specific position".format(len(positions)))
            print("  A: Close ALL positions")
            print("  R: Refresh")
            print("  Q: Quit")
            
            choice = input("\nChoice: ").strip().upper()
            
            if choice == 'Q':
                break
            elif choice == 'A':
                confirm = input("Close ALL positions? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    close_all_positions(connector)
                    break
            elif choice == 'R':
                continue
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(positions):
                    close_position(connector, positions[idx].ticket)
                    input("\nPress Enter to continue...")
                else:
                    print("Invalid position number")
            else:
                print("Invalid choice")
    
    finally:
        connector.disconnect()
        print("\n✓ Disconnected")


if __name__ == "__main__":
    main()
