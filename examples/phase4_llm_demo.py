"""
Phase 4 LLM Demo - AI-Powered Trading Analysis
Demonstrates LLM integration for market analysis and sentiment
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 80)
print("  PHASE 4: LLM INTEGRATION DEMONSTRATION")
print("=" * 80)

# Check if API keys are set
print("\n📦 Checking LLM configuration...")

# Import config loader
try:
    from src.utils.config_loader import get_openai_key, get_anthropic_key
    openai_key = get_openai_key()
    anthropic_key = get_anthropic_key()
except Exception as e:
    # Fallback to env vars only
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

has_openai = openai_key is not None and openai_key != ""
has_anthropic = anthropic_key is not None and anthropic_key != ""

if has_openai:
    print("✓ OpenAI API key found")
    # Check if key looks valid
    if openai_key.startswith('export ') or ' ' in openai_key:
        print("  ⚠️  Warning: Key appears to have 'export' prefix or spaces")
        print("  Fix: Remove 'export OPENAI_API_KEY=' from config/api_keys.yaml")
        print("  Should be just: api_key: \"sk-...\"") 
        has_openai = False
else:
    print("✗ OpenAI API key not set")
    print("  Set in config/api_keys.yaml OR OPENAI_API_KEY env var")

if has_anthropic:
    print("✓ Anthropic API key found")
else:
    print("✗ Anthropic API key not set (optional)")
    print("  Set in config/api_keys.yaml OR ANTHROPIC_API_KEY env var")

if not (has_openai or has_anthropic):
    print("\n⚠️  No LLM API keys configured!")
    print("Set at least one of:")
    print("  - OPENAI_API_KEY for GPT-4")
    print("  - ANTHROPIC_API_KEY for Claude")
    print("\nRunning in demo mode with mock data...")
    demo_mode = True
else:
    demo_mode = False

from src.llm import OPENAI_AVAILABLE, ANTHROPIC_AVAILABLE

if OPENAI_AVAILABLE:
    print("✓ OpenAI library installed")
else:
    print("✗ OpenAI library not installed (pip install openai)")

if ANTHROPIC_AVAILABLE:
    print("✓ Anthropic library installed")
else:
    print("✗ Anthropic library not installed (pip install anthropic)")


def generate_sample_data():
    """Generate sample market data"""
    print("\n📊 Generating sample market data...")
    
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')  # Use lowercase 'h'
    
    # Simulate EURUSD price movement
    price = 1.0800
    prices = []
    
    for _ in range(100):
        change = np.random.normal(0, 0.0003)
        price = price * (1 + change)
        prices.append(price)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * 1.0002 for p in prices],
        'low': [p * 0.9998 for p in prices],
        'close': prices,
        'volume': np.random.randint(100, 1000, 100)
    })
    
    print(f"✓ Generated 100 hourly candles for EURUSD")
    print(f"  Price range: {df['close'].min():.5f} - {df['close'].max():.5f}")
    
    return df


def demo_sentiment_analysis(llm_provider):
    """Demonstrate sentiment analysis"""
    print("\n" + "=" * 80)
    print("  1. SENTIMENT ANALYSIS")
    print("=" * 80)
    
    from src.llm import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer(llm_provider)
    
    # Sample news texts
    news_samples = [
        """
        ECB raises interest rates by 25 basis points, citing persistent inflation.
        The European Central Bank's hawkish stance strengthens the Euro against
        major currencies. Analysts expect further rate hikes in coming months.
        """,
        """
        US Dollar weakens as Fed signals pause in rate hikes. Market participants
        are pricing in potential rate cuts by year-end amid slowing economic growth.
        """,
        """
        EURUSD consolidates in tight range ahead of major economic data releases.
        Traders await US jobs report and European GDP figures. Market remains
        cautious with limited directional bias.
        """
    ]
    
    print("\n📰 Analyzing market sentiment from news sources...")
    
    for i, news in enumerate(news_samples, 1):
        print(f"\n--- News #{i} ---")
        print(news.strip()[:100] + "...")
        
        result = analyzer.analyze_text(news, symbol="EURUSD")
        
        print(f"\n  Sentiment: {result.sentiment.name}")
        print(f"  Confidence: {result.confidence:.0%}")
        print(f"  Signal: {result.trading_signal}")
        print(f"  Reasoning: {result.reasoning}")
        print(f"  Key Factors: {', '.join(result.key_factors)}")
    
    # Aggregate analysis
    print("\n📊 Aggregating sentiment from all sources...")
    aggregate = analyzer.analyze_multiple(news_samples, symbol="EURUSD")
    
    print(f"\n  Overall Sentiment: {aggregate.sentiment.name}")
    print(f"  Average Confidence: {aggregate.confidence:.0%}")
    print(f"  Trading Signal: {aggregate.trading_signal}")


def demo_market_analyst(llm_provider, bars):
    """Demonstrate AI market analyst"""
    print("\n" + "=" * 80)
    print("  2. AI MARKET ANALYST")
    print("=" * 80)
    
    from src.llm import MarketAnalyst
    
    analyst = MarketAnalyst(llm_provider)
    
    print("\n📈 Generating comprehensive market analysis...")
    
    analysis = analyst.analyze_market(
        symbol="EURUSD",
        bars=bars,
        additional_context="EUR showing strength on ECB rate hike expectations"
    )
    
    print("\n" + "-" * 80)
    print(analysis)
    print("-" * 80)
    
    # Trade explanation
    print("\n💡 Generating trade explanation...")
    
    explanation = analyst.explain_trade(
        symbol="EURUSD",
        signal_type="BUY",
        price=1.0850,
        stop_loss=1.0820,
        take_profit=1.0910
    )
    
    print(f"\n{explanation}")


def demo_daily_summary(llm_provider):
    """Demonstrate daily summary generation"""
    print("\n" + "=" * 80)
    print("  3. DAILY PERFORMANCE SUMMARY")
    print("=" * 80)
    
    from src.llm import MarketAnalyst
    
    analyst = MarketAnalyst(llm_provider)
    
    print("\n📊 Generating end-of-day trading summary...")
    
    summary = analyst.generate_daily_summary(
        trades_executed=8,
        win_rate=62.5,
        total_pnl=145.50,
        open_positions=2
    )
    
    print("\n" + "-" * 80)
    print(summary)
    print("-" * 80)


def main():
    """Run LLM demonstration"""
    
    # Generate sample data
    bars = generate_sample_data()
    
    # Check if we can run real LLM demos
    if demo_mode:
        print("\n" + "=" * 80)
        print("  DEMO MODE - API Keys Required for Live Demo")
        print("=" * 80)
        print("\nTo run the full LLM demo:")
        print("1. Get an API key from OpenAI or Anthropic")
        print("2. Set environment variable:")
        print("   - Windows: set OPENAI_API_KEY=your_key_here")
        print("   - Linux/Mac: export OPENAI_API_KEY=your_key_here")
        print("3. Re-run this script")
        
        print("\n📚 What the LLM features can do:")
        print("\n1. **Sentiment Analysis**")
        print("   - Analyze news and social media")
        print("   - Generate BUY/SELL/HOLD signals")
        print("   - Provide confidence scores")
        
        print("\n2. **AI Market Analyst**")
        print("   - Comprehensive market analysis")
        print("   - Trade recommendations with SL/TP")
        print("   - Risk assessment")
        
        print("\n3. **Trade Explanations**")
        print("   - Human-readable trade summaries")
        print("   - Risk/reward explanations")
        
        print("\n4. **Daily Summaries**")
        print("   - Performance analysis")
        print("   - Strengths and improvements")
        print("   - Tomorrow's outlook")
        
        return
    
    # Initialize LLM provider
    print("\n🤖 Initializing LLM provider...")
    
    if has_openai and OPENAI_AVAILABLE:
        from src.llm import OpenAIProvider
        llm = OpenAIProvider(model="gpt-4o-mini")  # or "gpt-4o" for full GPT-4
        print("✓ Using OpenAI GPT-4o-mini")
    elif has_anthropic and ANTHROPIC_AVAILABLE:
        from src.llm import AnthropicProvider
        llm = AnthropicProvider(model="claude-3-sonnet-20240229")
        print("✓ Using Anthropic Claude")
    else:
        print("✗ No LLM provider available")
        return
    
    # Run demos
    try:
        demo_sentiment_analysis(llm)
        demo_market_analyst(llm, bars)
        demo_daily_summary(llm)
        
        # Summary
        print("\n" + "=" * 80)
        print("  PHASE 4 SUMMARY")
        print("=" * 80)
        
        print("\n✅ LLM Integration Complete!")
        
        print("\n📦 Components:")
        print("  ✓ OpenAI & Anthropic providers")
        print("  ✓ Sentiment analyzer")
        print("  ✓ AI market analyst")
        print("  ✓ Trade explanations")
        print("  ✓ Daily summaries")
        
        print("\n🚀 Next Steps:")
        print("  1. Integrate sentiment into trading strategy")
        print("  2. Add real-time news feed parsing")
        print("  3. Implement natural language trade interface")
        print("  4. Create automated market reports")
        
        print("\n📖 See PHASE4_COMPLETE.md for full documentation")
        
    except Exception as e:
        error_msg = str(e)
        
        print("\n" + "=" * 80)
        print("  ⚠️  DEMO ERROR")
        print("=" * 80)
        
        if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
            print("\n❌ OpenAI API Quota Exceeded")
            print("\nYour OpenAI account has run out of credits.")
            print("\n🔧 How to fix:")
            print("  1. Go to https://platform.openai.com/account/billing")
            print("  2. Add a payment method")
            print("  3. Add $5-10 credits (will last months)")
            print("\n💰 Cost for this bot: ~$0.40/month")
            print("   (Very affordable - gpt-4o-mini is cheap!)")
            print("\n📖 See docs/API_SETUP.md for detailed setup")
            
        elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
            print("\n❌ Invalid API Key")
            print("\n🔧 How to fix:")
            print("  1. Check your API key in config/api_keys.yaml")
            print("  2. Make sure it starts with 'sk-proj-' or 'sk-'")
            print("  3. Create new key at https://platform.openai.com/api-keys")
            print("\n📖 See docs/API_SETUP.md for detailed setup")
            
        elif "rate_limit" in error_msg.lower():
            print("\n❌ Rate Limit Exceeded")
            print("\nYou're making requests too fast.")
            print("\n🔧 How to fix:")
            print("  1. Wait 60 seconds and try again")
            print("  2. Reduce request frequency")
            print("  3. Upgrade your OpenAI tier")
            
        else:
            print(f"\n❌ Error: {error_msg}")
            print("\n📖 See docs/API_SETUP.md for troubleshooting")
        
        print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
