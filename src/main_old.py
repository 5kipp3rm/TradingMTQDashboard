"""
CLI Interface for TradingMTQ
Interactive command-line interface for trading operations
"""
import sys
import time
from typing import Optional
from datetime import datetime

from .connectors import (
    ConnectorFactory, PlatformType, OrderType,
    create_mt5_connector, get_connector
)
from .trading import TradingController
from .utils import setup_logging, get_config, get_logger


logger = get_logger(__name__)


class TradingCLI:
    """Interactive CLI for trading operations"""
    
    def __init__(self):
        """Initialize CLI and auto-connect"""
        self.controller: Optional[TradingController] = None
        self.connector = None
        self.config = get_config()
        self.running = True
        
        logger.info("TradingCLI initialized")
        
        # Auto-connect on startup
        self._auto_connect()
    
    def _auto_connect(self):
        """Automatically connect to MT5 on startup"""
        credentials = self.config.get_mt5_credentials()
        
        if not credentials['login'] or not credentials['password']:
            logger.error("MT5 credentials not found in .env file")
            print("\n\033[33m⚠ Warning: MT5 credentials not configured in .env\033[0m")
            print("Please configure MT5_LOGIN, MT5_PASSWORD, and MT5_SERVER in .env file")
            return
        
        logger.info(f"Auto-connecting to MT5 server: {credentials['server']}")
        print(f"\n🔄 Connecting to MT5 ({credentials['server']})...")
        
        try:
            # Create connector
            self.connector = create_mt5_connector("main")
            
            # Connect
            success = self.connector.connect(**credentials)
            
            if success:
                # Create controller
                self.controller = TradingController(self.connector)
                
                # Get account info
                account = self.connector.get_account_info()
                
                print(f"\033[32m✓ Connected successfully!\033[0m")
                print(f"Account: {account.login} | Balance: ${account.balance:,.2f} | Leverage: 1:{account.leverage}\n")
                logger.info(f"Connected to account {account.login}")
            else:
                print("\033[31m✗ Connection failed!\033[0m")
                print("Please ensure MT5 terminal is running and logged in.\n")
                logger.error("Failed to connect to MT5")
                self.connector = None
                self.controller = None
        
        except Exception as e:
            print(f"\033[31m✗ Connection error: {e}\033[0m\n")
            logger.error(f"Connection error: {e}", exc_info=True)
            self.connector = None
            self.controller = None
    
    def clear_screen(self):
        """Clear console screen"""
        print("\033[2J\033[H", end="")
    
    def print_header(self):
        """Print application header"""
        print("=" * 60)
        print(" " * 15 + "TradingMTQ - Phase 1")
        print("=" * 60)
        if self.connector and self.connector.is_connected():
            account = self.connector.get_account_info()
            status = f"✓ {account.server} | Account: {account.login}"
            print(f"Status: \033[32m{status}\033[0m")
            print(f"Balance: ${account.balance:,.2f} | Equity: ${account.equity:,.2f}")
        else:
            print("Status: \033[31m✗ Not Connected\033[0m")
        print("=" * 60)
        print()
    
    def print_menu(self):
        """Print main menu"""
        print("Main Menu:")
        print("  1. View Account Info")
        print("  2. List Currency Pairs")
        print("  3. View Real-Time Prices")
        print("  4. Place Market Order")
        print("  5. View Open Positions")
        print("  6. Close Position")
        print("  7. Modify Position")
        print("  8. Close All Positions")
        print("  0. Exit")
        print()
    
    def view_account_info(self):
        """View account information"""
        if not self._check_connection():
            return
        
        print("\n" + "=" * 60)
        print("Account Information")
        print("=" * 60)
        
        account = self.connector.get_account_info()
        if not account:
            print("\n\033[31mFailed to get account information\033[0m")
            input("\nPress Enter to continue...")
            return
        
        summary = self.controller.get_account_summary()
        
        print(f"\n Account Details:")
        print(f"  Login:          {account.login}")
        print(f"  Server:         {account.server}")
        print(f"  Company:        {account.company}")
        print(f"  Name:           {account.name}")
        print()
        print(f" Financial:")
        print(f"  Balance:        ${account.balance:,.2f} {account.currency}")
        print(f"  Equity:         ${account.equity:,.2f} {account.currency}")
        print(f"  Profit:         ${account.profit:,.2f} {account.currency}")
        print(f"  Margin:         ${account.margin:,.2f} {account.currency}")
        print(f"  Free Margin:    ${account.margin_free:,.2f} {account.currency}")
        print(f"  Margin Level:   {account.margin_level:.2f}%")
        print()
        print(f" Trading:")
        print(f"  Leverage:       1:{account.leverage}")
        print(f"  Trade Allowed:  {'Yes' if account.trade_allowed else 'No'}")
        print(f"  Open Positions: {summary['open_positions']}")
        print(f"  Total Volume:   {summary['total_volume']:.2f} lots")
        
        input("\nPress Enter to continue...")
    
    def list_currency_pairs(self):
        """List available currency pairs"""
        if not self._check_connection():
            return
        
        print("\n" + "=" * 60)
        print("Available Currency Pairs")
        print("=" * 60)
        
        print("\nFetching symbols...")
        symbols = self.connector.get_symbols("Forex*")
        
        if not symbols:
            print("\n\033[31mNo forex symbols found\033[0m")
            input("\nPress Enter to continue...")
            return
        
        # Display first 20 symbols
        print(f"\nShowing {min(20, len(symbols))} of {len(symbols)} symbols:\n")
        print(f"{'Symbol':<12} {'Bid':<12} {'Ask':<12} {'Spread':<10}")
        print("-" * 50)
        
        for i, symbol in enumerate(symbols[:20]):
            tick = self.connector.get_tick(symbol)
            if tick:
                spread_pips = tick.spread * 10000  # Convert to pips
                print(f"{symbol:<12} {tick.bid:<12.5f} {tick.ask:<12.5f} {spread_pips:<10.1f}")
        
        input("\nPress Enter to continue...")
    
    def view_realtime_prices(self):
        """View real-time prices for a symbol"""
        if not self._check_connection():
            return
        
        print("\n" + "=" * 60)
        print("Real-Time Prices")
        print("=" * 60)
        
        symbol = input("\nEnter symbol (e.g., EURUSD): ").strip().upper()
        
        if not symbol:
            return
        
        # Verify symbol exists
        symbol_info = self.connector.get_symbol_info(symbol)
        if not symbol_info:
            print(f"\n\033[31mSymbol {symbol} not found\033[0m")
            input("\nPress Enter to continue...")
            return
        
        print(f"\nReal-Time Prices for {symbol}")
        print(f"Description: {symbol_info.description}")
        print("\nPress Ctrl+C to stop\n")
        print(f"{'Time':<20} {'Bid':<12} {'Ask':<12} {'Spread':<10}")
        print("-" * 60)
        
        try:
            while True:
                tick = self.connector.get_tick(symbol)
                if tick:
                    spread_pips = tick.spread * 10000
                    time_str = tick.time.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{time_str:<20} {tick.bid:<12.5f} {tick.ask:<12.5f} {spread_pips:<10.1f}", end="\r")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopped.")
        
        input("\nPress Enter to continue...")
    
    def place_market_order(self):
        """Place a market order"""
        if not self._check_connection():
            return
        
        print("\n" + "=" * 60)
        print("Place Market Order")
        print("=" * 60)
        
        try:
            # Get order details
            symbol = input("\nEnter symbol (e.g., EURUSD): ").strip().upper()
            if not symbol:
                return
            
            # Verify symbol
            symbol_info = self.connector.get_symbol_info(symbol)
            if not symbol_info:
                print(f"\n\033[31mSymbol {symbol} not found\033[0m")
                input("\nPress Enter to continue...")
                return
            
            action = input("Enter action (BUY/SELL): ").strip().upper()
            if action not in ['BUY', 'SELL']:
                print("\n\033[31mInvalid action. Must be BUY or SELL\033[0m")
                input("\nPress Enter to continue...")
                return
            
            order_type = OrderType.BUY if action == 'BUY' else OrderType.SELL
            
            volume_str = input(f"Enter volume in lots (min: {symbol_info.volume_min}): ").strip()
            volume = float(volume_str)
            
            sl_str = input("Enter stop loss price (press Enter to skip): ").strip()
            sl = float(sl_str) if sl_str else None
            
            tp_str = input("Enter take profit price (press Enter to skip): ").strip()
            tp = float(tp_str) if tp_str else None
            
            # Show confirmation
            print("\n" + "-" * 60)
            print("Order Confirmation:")
            print(f"  Symbol:       {symbol}")
            print(f"  Action:       {action}")
            print(f"  Volume:       {volume} lots")
            print(f"  Current Bid:  {symbol_info.bid:.5f}")
            print(f"  Current Ask:  {symbol_info.ask:.5f}")
            if sl:
                print(f"  Stop Loss:    {sl:.5f}")
            if tp:
                print(f"  Take Profit:  {tp:.5f}")
            print("-" * 60)
            
            confirm = input("\nExecute order? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("\nOrder cancelled.")
                input("\nPress Enter to continue...")
                return
            
            # Execute trade
            print("\nExecuting order...")
            result = self.controller.execute_trade(
                symbol=symbol,
                action=order_type,
                volume=volume,
                sl=sl,
                tp=tp,
                comment="Manual CLI order"
            )
            
            if result.success:
                print("\n\033[32m✓ Order executed successfully!\033[0m")
                print(f"  Ticket:       {result.order_ticket}")
                print(f"  Price:        {result.price:.5f}")
                print(f"  Volume:       {result.volume} lots")
                print(f"  Time:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("\n\033[31m✗ Order execution failed!\033[0m")
                print(f"  Error:        {result.error_message}")
        
        except ValueError as e:
            print(f"\n\033[31mInvalid input: {e}\033[0m")
        except Exception as e:
            print(f"\n\033[31mError: {e}\033[0m")
            logger.error(f"Error placing order: {e}", exc_info=True)
        
        input("\nPress Enter to continue...")
    
    def view_open_positions(self):
        """View open positions"""
        if not self._check_connection():
            return
        
        print("\n" + "=" * 60)
        print("Open Positions")
        print("=" * 60)
        
        positions = self.controller.get_open_positions()
        
        if not positions:
            print("\n\033[33mNo open positions\033[0m")
            input("\nPress Enter to continue...")
            return
        
        print(f"\n{len(positions)} open position(s):\n")
        print(f"{'Ticket':<10} {'Symbol':<10} {'Type':<6} {'Volume':<8} {'Open':<12} {'Current':<12} {'P&L':<12}")
        print("-" * 80)
        
        total_profit = 0
        for pos in positions:
            profit_color = "\033[32m" if pos.profit >= 0 else "\033[31m"
            reset_color = "\033[0m"
            
            print(f"{pos.ticket:<10} {pos.symbol:<10} {pos.type.value:<6} {pos.volume:<8.2f} "
                  f"{pos.price_open:<12.5f} {pos.price_current:<12.5f} "
                  f"{profit_color}{pos.profit:<12.2f}{reset_color}")
            
            total_profit += pos.profit
        
        print("-" * 80)
        total_color = "\033[32m" if total_profit >= 0 else "\033[31m"
        print(f"{'Total P&L:':<68} {total_color}{total_profit:.2f}\033[0m")
        
        input("\nPress Enter to continue...")
    
    def close_position(self):
        """Close a specific position"""
        if not self._check_connection():
            return
        
        print("\n" + "=" * 60)
        print("Close Position")
        print("=" * 60)
        
        # Show positions first
        positions = self.controller.get_open_positions()
        if not positions:
            print("\n\033[33mNo open positions\033[0m")
            input("\nPress Enter to continue...")
            return
        
        print("\nOpen positions:")
        for pos in positions:
            print(f"  Ticket: {pos.ticket} - {pos.symbol} {pos.type.value} {pos.volume} lots - P&L: ${pos.profit:.2f}")
        
        try:
            ticket_str = input("\nEnter ticket number to close: ").strip()
            if not ticket_str:
                return
            
            ticket = int(ticket_str)
            
            # Confirm
            confirm = input(f"\nClose position {ticket}? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("\nCancelled.")
                input("\nPress Enter to continue...")
                return
            
            print("\nClosing position...")
            result = self.controller.close_trade(ticket)
            
            if result.success:
                print("\n\033[32m✓ Position closed successfully!\033[0m")
                print(f"  Close Price:  {result.price:.5f}")
                print(f"  Time:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("\n\033[31m✗ Failed to close position!\033[0m")
                print(f"  Error:        {result.error_message}")
        
        except ValueError:
            print("\n\033[31mInvalid ticket number\033[0m")
        except Exception as e:
            print(f"\n\033[31mError: {e}\033[0m")
            logger.error(f"Error closing position: {e}", exc_info=True)
        
        input("\nPress Enter to continue...")
    
    def modify_position(self):
        """Modify position SL/TP"""
        if not self._check_connection():
            return
        
        print("\n" + "=" * 60)
        print("Modify Position")
        print("=" * 60)
        
        # Show positions
        positions = self.controller.get_open_positions()
        if not positions:
            print("\n\033[33mNo open positions\033[0m")
            input("\nPress Enter to continue...")
            return
        
        print("\nOpen positions:")
        for pos in positions:
            print(f"  Ticket: {pos.ticket} - {pos.symbol} {pos.type.value} - SL: {pos.sl} TP: {pos.tp}")
        
        try:
            ticket = int(input("\nEnter ticket number: ").strip())
            
            sl_str = input("Enter new stop loss (press Enter to keep current): ").strip()
            sl = float(sl_str) if sl_str else None
            
            tp_str = input("Enter new take profit (press Enter to keep current): ").strip()
            tp = float(tp_str) if tp_str else None
            
            if sl is None and tp is None:
                print("\nNo changes specified.")
                input("\nPress Enter to continue...")
                return
            
            print("\nModifying position...")
            result = self.controller.modify_trade(ticket, sl, tp)
            
            if result.success:
                print("\n\033[32m✓ Position modified successfully!\033[0m")
            else:
                print("\n\033[31m✗ Failed to modify position!\033[0m")
                print(f"  Error: {result.error_message}")
        
        except ValueError as e:
            print(f"\n\033[31mInvalid input: {e}\033[0m")
        except Exception as e:
            print(f"\n\033[31mError: {e}\033[0m")
            logger.error(f"Error modifying position: {e}", exc_info=True)
        
        input("\nPress Enter to continue...")
    
    def close_all_positions(self):
        """Close all open positions"""
        if not self._check_connection():
            return
        
        print("\n" + "=" * 60)
        print("Close All Positions")
        print("=" * 60)
        
        positions = self.controller.get_open_positions()
        if not positions:
            print("\n\033[33mNo open positions\033[0m")
            input("\nPress Enter to continue...")
            return
        
        print(f"\n{len(positions)} open position(s) will be closed.")
        confirm = input("\nAre you sure? This cannot be undone! (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("\nCancelled.")
            input("\nPress Enter to continue...")
            return
        
        print("\nClosing all positions...")
        results = self.controller.close_all_positions()
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        print(f"\n\033[32m✓ Closed {successful} position(s)\033[0m")
        if failed > 0:
            print(f"\033[31m✗ Failed to close {failed} position(s)\033[0m")
        
        input("\nPress Enter to continue...")
    
    def _check_connection(self) -> bool:
        """Check if connected to MT5"""
        if not self.connector or not self.connector.is_connected():
            print("\n\033[31m✗ Not connected to MetaTrader\033[0m")
            print("Please check .env configuration and ensure MT5 terminal is running.")
            input("\nPress Enter to continue...")
            return False
        return True
    
    def run(self):
        """Run the CLI"""
        try:
            while self.running:
                self.clear_screen()
                self.print_header()
                self.print_menu()
                
                choice = input("Enter your choice: ").strip()
                
                if choice == '1':
                    self.view_account_info()
                elif choice == '2':
                    self.list_currency_pairs()
                elif choice == '3':
                    self.view_realtime_prices()
                elif choice == '4':
                    self.place_market_order()
                elif choice == '5':
                    self.view_open_positions()
                elif choice == '6':
                    self.close_position()
                elif choice == '7':
                    self.modify_position()
                elif choice == '8':
                    self.close_all_positions()
                elif choice == '0':
                    if self.connector:
                        self.disconnect()
                    print("\nExiting TradingMTQ. Goodbye!")
                    self.running = False
                else:
                    print("\n\033[31mInvalid choice. Please try again.\033[0m")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            if self.connector:
                self.connector.disconnect()
        except Exception as e:
            print(f"\n\033[31mUnexpected error: {e}\033[0m")
            logger.error(f"CLI error: {e}", exc_info=True)
            if self.connector:
                self.connector.disconnect()


def main():
    """Main entry point"""
    # Setup logging
    setup_logging(log_level="INFO")
    
    logger.info("Starting TradingMTQ CLI")
    
    # Run CLI
    cli = TradingCLI()
    cli.run()
    
    logger.info("TradingMTQ CLI terminated")


if __name__ == '__main__':
    main()
