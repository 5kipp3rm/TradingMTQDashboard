#!/usr/bin/env python
"""
Check .env Configuration
Verifies your .env file has the necessary credentials
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    print("\n" + "=" * 80)
    print("  .ENV CONFIGURATION CHECK")
    print("=" * 80)
    
    env_file = Path(__file__).parent / '.env'
    
    # Check if .env exists
    if not env_file.exists():
        print("\n❌ .env file NOT FOUND!")
        print("\n💡 SOLUTION:")
        print("   1. Copy .env.example to .env:")
        print("      $ cp .env.example .env")
        print("\n   2. Edit .env and add your credentials:")
        print("      MT5_LOGIN=your_account_number")
        print("      MT5_PASSWORD=your_password")
        print("      MT5_SERVER=your_broker_server")
        print("\n" + "=" * 80 + "\n")
        return False
    
    print(f"\n✓ .env file found at: {env_file}")
    
    # Load environment variables
    load_dotenv(env_file)
    
    # Check required variables
    print("\n🔍 Checking credentials...")
    
    required_vars = {
        'MT5_LOGIN': 'MT5 Login (account number)',
        'MT5_PASSWORD': 'MT5 Password',
        'MT5_SERVER': 'MT5 Server',
    }
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        
        if not value or value == f'your_{var.lower()}_here' or 'your_' in value:
            print(f"  ✗ {var:<15} - NOT SET or using placeholder")
            print(f"    ({description})")
            all_set = False
        else:
            # Mask password
            if 'PASSWORD' in var:
                display_value = '*' * len(value)
            else:
                display_value = value
            print(f"  ✓ {var:<15} = {display_value}")
    
    print("\n" + "-" * 80)
    
    if all_set:
        print("\n🎉 ALL CREDENTIALS CONFIGURED!")
        print("\n📋 NEXT STEPS:")
        print("   1. Open MetaTrader 5 application (keep it running)")
        print("   2. Run: python run.py")
        print("\n" + "=" * 80 + "\n")
        return True
    else:
        print("\n⚠️  SOME CREDENTIALS MISSING!")
        print("\n💡 FIX:")
        print(f"   Edit {env_file} and set the missing values")
        print("\n   Example:")
        print("   MT5_LOGIN=12345678")
        print("   MT5_PASSWORD=MySecurePassword")
        print("   MT5_SERVER=MetaQuotes-Demo")
        print("\n" + "=" * 80 + "\n")
        return False


if __name__ == "__main__":
    main()
