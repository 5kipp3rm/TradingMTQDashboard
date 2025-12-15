#!/usr/bin/env python3
"""
Add Trading Account Script

Easily add MT5 trading accounts to the database.

Usage:
    python scripts/add_account.py --demo
    python scripts/add_account.py --live
    python scripts/add_account.py --interactive
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Python 3.14 compatibility
from src.utils.python314_compat import *  # noqa

import argparse
from decimal import Decimal
from src.database.connection import init_db, get_session
from src.database.models import TradingAccount


def add_account_interactive():
    """Add account with interactive prompts"""
    print("\n=== Add Trading Account ===\n")

    # Required fields
    account_number = int(input("MT5 Account Number: "))
    account_name = input("Account Name (e.g., 'Main Trading Account'): ")
    broker = input("Broker Name (e.g., 'IC Markets'): ")
    server = input("MT5 Server (e.g., 'ICMarkets-Demo'): ")
    login = int(input(f"Login Number (default: {account_number}): ") or account_number)

    # Optional fields
    is_demo = input("Is this a demo account? (y/n, default: y): ").lower() != 'n'
    is_active = input("Activate account? (y/n, default: y): ").lower() != 'n'
    is_default = input("Set as default account? (y/n, default: n): ").lower() == 'y'

    initial_balance = input("Initial Balance (optional, e.g., 10000): ")
    initial_balance = Decimal(initial_balance) if initial_balance else None

    currency = input("Currency (default: USD): ") or "USD"
    description = input("Description (optional): ") or None

    return create_account(
        account_number=account_number,
        account_name=account_name,
        broker=broker,
        server=server,
        login=login,
        is_demo=is_demo,
        is_active=is_active,
        is_default=is_default,
        initial_balance=initial_balance,
        currency=currency,
        description=description
    )


def add_demo_account():
    """Add a demo account with preset values"""
    return create_account(
        account_number=12345678,
        account_name="Demo Account",
        broker="Demo Broker",
        server="DemoServer-MT5",
        login=12345678,
        is_demo=True,
        is_active=True,
        is_default=True,
        initial_balance=Decimal("10000.00"),
        currency="USD",
        description="Demo account for testing"
    )


def add_live_account():
    """Add a live account with interactive prompts for sensitive data"""
    print("\n=== Add LIVE Trading Account ===")
    print("⚠️  WARNING: This will add a LIVE trading account!\n")

    confirm = input("Are you sure you want to add a LIVE account? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return None

    account_number = int(input("MT5 Account Number: "))
    account_name = input("Account Name: ")
    broker = input("Broker Name: ")
    server = input("MT5 Server: ")
    login = int(input(f"Login Number (default: {account_number}): ") or account_number)

    initial_balance = input("Initial Balance: ")
    initial_balance = Decimal(initial_balance) if initial_balance else None

    currency = input("Currency (default: USD): ") or "USD"
    description = input("Description (optional): ") or None

    return create_account(
        account_number=account_number,
        account_name=account_name,
        broker=broker,
        server=server,
        login=login,
        is_demo=False,  # LIVE account
        is_active=True,
        is_default=False,
        initial_balance=initial_balance,
        currency=currency,
        description=description
    )


def create_account(**kwargs):
    """Create account in database"""
    # Initialize database
    init_db()

    # Create account
    with next(get_session()) as db:
        # Check if account already exists
        existing = db.query(TradingAccount).filter_by(
            account_number=kwargs['account_number']
        ).first()

        if existing:
            print(f"\n❌ Account {kwargs['account_number']} already exists!")
            print(f"   Name: {existing.account_name}")
            print(f"   ID: {existing.id}")
            return None

        # Create new account
        account = TradingAccount(**kwargs)
        db.add(account)
        db.commit()
        db.refresh(account)

        print("\n✅ Account created successfully!")
        print(f"   ID: {account.id}")
        print(f"   Account Number: {account.account_number}")
        print(f"   Name: {account.account_name}")
        print(f"   Broker: {account.broker}")
        print(f"   Server: {account.server}")
        print(f"   Type: {'DEMO' if account.is_demo else 'LIVE'}")
        print(f"   Active: {account.is_active}")
        print(f"   Default: {account.is_default}")
        if account.initial_balance:
            print(f"   Initial Balance: {account.initial_balance} {account.currency}")

        return account


def list_accounts():
    """List all accounts in database"""
    init_db()

    with next(get_session()) as db:
        accounts = db.query(TradingAccount).all()

        if not accounts:
            print("\nNo accounts found in database.")
            return

        print(f"\n=== Trading Accounts ({len(accounts)}) ===\n")

        for acc in accounts:
            status = "✓ ACTIVE" if acc.is_active else "✗ INACTIVE"
            acc_type = "DEMO" if acc.is_demo else "LIVE"
            default = " [DEFAULT]" if acc.is_default else ""

            print(f"ID: {acc.id} | {acc.account_number} | {acc.account_name}")
            print(f"  Broker: {acc.broker} | Server: {acc.server}")
            print(f"  Type: {acc_type} | Status: {status}{default}")
            if acc.initial_balance:
                print(f"  Balance: {acc.initial_balance} {acc.currency}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Add MT5 trading accounts to database'
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--interactive', '-i', action='store_true',
                      help='Add account with interactive prompts')
    group.add_argument('--demo', '-d', action='store_true',
                      help='Add demo account with preset values')
    group.add_argument('--live', '-l', action='store_true',
                      help='Add live account (interactive)')
    group.add_argument('--list', action='store_true',
                      help='List all accounts')

    args = parser.parse_args()

    try:
        if args.list:
            list_accounts()
        elif args.demo:
            add_demo_account()
        elif args.live:
            add_live_account()
        elif args.interactive:
            add_account_interactive()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
