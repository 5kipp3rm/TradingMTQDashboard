# API Setup Guide

## Quick Start

### 1. Add Your OpenAI API Key

Edit `config/api_keys.yaml`:

```yaml
openai:
  api_key: "sk-proj-your-actual-key-here"  # Replace with your key
  default_model: "gpt-4o-mini"
```

### 2. Get Your API Key

**If you don't have an OpenAI account yet:**

1. Go to https://platform.openai.com/signup
2. Sign up (get $5 free credit)
3. Go to https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-proj-...`)
6. Paste into `config/api_keys.yaml`

### 3. Check Your Quota

**The error you got means:**
- Your free $5 credit has been used up, OR
- You haven't added a payment method

**To fix:**

1. Go to https://platform.openai.com/account/billing
2. Check your credit balance
3. If $0, add a payment method

**Expected costs for trading bot:**
- **gpt-4o-mini**: ~$0.0004 per analysis
- **Daily usage**: ~10-50 analyses = $0.004-0.02/day
- **Monthly**: ~$0.12-0.60/month (very cheap!)

### 4. Alternative: Use Anthropic Claude

If you don't want to pay for OpenAI, try Anthropic:

```yaml
anthropic:
  api_key: "sk-ant-your-key-here"
  default_model: "claude-3-sonnet-20240229"
```

Get key from: https://console.anthropic.com/

## Three Ways to Set API Keys

### Option 1: Config File (Recommended)

Edit `config/api_keys.yaml`:
```yaml
openai:
  api_key: "sk-proj-..."
```

✅ **Pros**: Easy, persistent, organized  
❌ **Cons**: Must protect file (don't commit to git)

### Option 2: Environment Variable

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY = "sk-proj-..."

# Windows (CMD)
set OPENAI_API_KEY=sk-proj-...

# Linux/Mac
export OPENAI_API_KEY=sk-proj-...
```

✅ **Pros**: Most secure, no files to protect  
❌ **Cons**: Need to set every session

### Option 3: Code Parameter

```python
from src.llm import OpenAIProvider

llm = OpenAIProvider(api_key="sk-proj-...")
```

✅ **Pros**: Explicit  
❌ **Cons**: Hard-coded in code (bad practice)

## Priority Order

The system checks in this order:
1. **Environment variable** (highest priority)
2. **Config file** (`config/api_keys.yaml`)
3. **Code parameter**

So if you set `OPENAI_API_KEY` env var, it will use that even if config file has a different key.

## Demo Mode (No API Key)

If you don't set any key, the demo runs in "mock mode":

```bash
python examples/phase4_llm_demo.py
```

Output:
```
⚠️  No LLM API keys configured!
Running in demo mode with mock data...
```

It will show what the features can do without making real API calls.

## Troubleshooting

### Error: "insufficient_quota"

**Problem**: No credits left or no payment method

**Solution**:
1. Go to https://platform.openai.com/account/billing
2. Add payment method
3. Add $5-10 credits (will last months for this bot)

### Error: "invalid_api_key"

**Problem**: Wrong key or expired

**Solution**:
1. Go to https://platform.openai.com/api-keys
2. Create a new key
3. Copy the full key including `sk-proj-` prefix
4. Update config file

### Error: "model_not_found"

**Problem**: Using old model name

**Solution**: Use current models:
- `gpt-4o` (most capable)
- `gpt-4o-mini` (recommended)
- `gpt-3.5-turbo` (legacy)

### Warning: FutureWarning: 'H' is deprecated

**Fixed!** Updated to use lowercase `'h'` instead of `'H'`.

## Cost Calculator

**gpt-4o-mini** (recommended):
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- Typical analysis: 500 input + 300 output tokens

**Per analysis cost:**
```
(500 × $0.15 / 1M) + (300 × $0.60 / 1M) = $0.00026
```

**Monthly cost** (50 analyses/day):
```
50 × 30 × $0.00026 = $0.39/month
```

**Very affordable!**

## Security Best Practices

### ✅ DO:
- Store keys in `config/api_keys.yaml` (protected by .gitignore)
- Use environment variables for production
- Rotate keys periodically
- Set usage limits in OpenAI dashboard

### ❌ DON'T:
- Commit `api_keys.yaml` to git (already in .gitignore)
- Share keys in screenshots/logs
- Hard-code keys in Python files
- Use keys in public repos

## Next Steps

1. **Add your OpenAI key** to `config/api_keys.yaml`
2. **Run the demo**: `python examples/phase4_llm_demo.py`
3. **Check it works**: Should see sentiment analysis results
4. **Start using**: Integrate into your trading strategies!

## Support

If you still have issues:
1. Check OpenAI status: https://status.openai.com/
2. Verify key works: https://platform.openai.com/playground
3. Check billing: https://platform.openai.com/account/billing
