"""
Trading Commands Module
Placeholder for run_trading function that will be imported by app.py
"""


def run_trading(config_file: str, aggressive: bool = False, demo: bool = False,
                interval: int = None, max_concurrent: int = None,
                enable_ml: bool = True, enable_llm: bool = True):
    """
    Run configuration-based multi-currency trading
    
    This function calls the legacy trading logic from main.py
    """
    print(f"\nStarting trading...")
    print(f"   Config: {config_file}")
    if aggressive:
        print(f"   Mode: AGGRESSIVE")
    if demo:
        print(f"   Demo: YES")
    if interval:
        print(f"   Interval: {interval}s")
    if max_concurrent:
        print(f"   Max Concurrent: {max_concurrent}")
    print(f"   ML Enhancement: {'ENABLED' if enable_ml else 'DISABLED'}")
    print(f"   LLM Sentiment: {'ENABLED' if enable_llm else 'DISABLED'}")
    print()
    
    # Import and run the legacy trading function
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from main import _run_legacy_trading
    _run_legacy_trading(enable_ml=enable_ml, enable_llm=enable_llm)
