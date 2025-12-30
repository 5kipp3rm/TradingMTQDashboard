#!/usr/bin/env python3
"""
Seed default currency configurations into the database
"""
import sys

# Add src to path
sys.path.insert(0, '/Users/mfinkels/CodePlatform/PersonalCode/TradingMTQ')

from src.database import init_db, CurrencyConfiguration
from src.database.connection import get_session_factory

def seed_default_currencies():
    """Seed default currency configurations"""
    
    # Initialize database
    init_db()
    
    # Get session factory
    SessionFactory = get_session_factory()
    session = SessionFactory()
    
    # Default currencies with common trading configurations
    default_currencies = [
        {
            "symbol": "EURUSD",
            "enabled": True,
            "risk_percent": 1.0,
            "max_position_size": 1.0,
            "min_position_size": 0.01,
            "strategy_type": "crossover",
            "timeframe": "M15",
            "fast_period": 10,
            "slow_period": 20,
            "sl_pips": 50,
            "tp_pips": 100,
            "cooldown_seconds": 300,
            "trade_on_signal_change": True,
            "allow_position_stacking": False,
            "max_positions_same_direction": 1,
            "max_total_positions": 5,
            "stacking_risk_multiplier": 1.0,
            "description": "Euro vs US Dollar - Most traded currency pair"
        },
        {
            "symbol": "GBPUSD",
            "enabled": True,
            "risk_percent": 1.0,
            "max_position_size": 1.0,
            "min_position_size": 0.01,
            "strategy_type": "crossover",
            "timeframe": "M15",
            "fast_period": 10,
            "slow_period": 20,
            "sl_pips": 60,
            "tp_pips": 120,
            "cooldown_seconds": 300,
            "trade_on_signal_change": True,
            "allow_position_stacking": False,
            "max_positions_same_direction": 1,
            "max_total_positions": 5,
            "stacking_risk_multiplier": 1.0,
            "description": "British Pound vs US Dollar"
        },
        {
            "symbol": "USDJPY",
            "enabled": True,
            "risk_percent": 1.0,
            "max_position_size": 1.0,
            "min_position_size": 0.01,
            "strategy_type": "crossover",
            "timeframe": "M15",
            "fast_period": 10,
            "slow_period": 20,
            "sl_pips": 40,
            "tp_pips": 80,
            "cooldown_seconds": 300,
            "trade_on_signal_change": True,
            "allow_position_stacking": False,
            "max_positions_same_direction": 1,
            "max_total_positions": 5,
            "stacking_risk_multiplier": 1.0,
            "description": "US Dollar vs Japanese Yen"
        },
        {
            "symbol": "AUDUSD",
            "enabled": True,
            "risk_percent": 1.0,
            "max_position_size": 1.0,
            "min_position_size": 0.01,
            "strategy_type": "crossover",
            "timeframe": "M15",
            "fast_period": 10,
            "slow_period": 20,
            "sl_pips": 50,
            "tp_pips": 100,
            "cooldown_seconds": 300,
            "trade_on_signal_change": True,
            "allow_position_stacking": False,
            "max_positions_same_direction": 1,
            "max_total_positions": 5,
            "stacking_risk_multiplier": 1.0,
            "description": "Australian Dollar vs US Dollar"
        }
    ]
    
    try:
        added_count = 0
        for currency_data in default_currencies:
            # Check if already exists
            existing = session.query(CurrencyConfiguration).filter_by(
                symbol=currency_data["symbol"]
            ).first()
            
            if not existing:
                currency = CurrencyConfiguration(**currency_data)
                session.add(currency)
                added_count += 1
                print(f"✓ Added {currency_data['symbol']}")
            else:
                print(f"- {currency_data['symbol']} already exists, skipping")
        
        session.commit()
        print(f"\n✅ Successfully seeded {added_count} currencies")
        
        # Show all currencies
        all_currencies = session.query(CurrencyConfiguration).all()
        print(f"\nTotal currencies in database: {len(all_currencies)}")
        for c in all_currencies:
            status = "✓ enabled" if c.enabled else "✗ disabled"
            print(f"  - {c.symbol}: {status}")
            
    except Exception as e:
        print(f"\n❌ Error seeding currencies: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_default_currencies()
