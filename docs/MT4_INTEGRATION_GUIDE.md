# MT4 Integration Guide

This document provides three different approaches to integrate MetaTrader 4 (MT4) with TradingMTQ.

## Overview

MT4 does not have official Python API support like MT5. However, there are several viable approaches:

1. **Python Package (MetaTrader4)** - Third-party Python wrapper
2. **FIX API Integration** - Professional trading protocol
3. **Bridge Solution** - MQL4 Expert Advisor + HTTP/Socket communication

---

## Approach 1: MetaTrader4 Python Package

### Installation

```bash
pip install MetaTrader4
```

### Pros
- Direct Python integration
- Similar API to MT5
- Relatively simple implementation

### Cons
- Third-party package (not official)
- Limited broker support
- Less mature than MT5 package
- May require specific broker configurations

### Implementation Status
See `src/connectors/mt4_connector_v1.py` for implementation using this approach.

---

## Approach 2: FIX API Integration

### Overview
Financial Information eXchange (FIX) protocol is a professional industry standard for electronic trading.

### Requirements
1. Broker must support FIX API
2. FIX credentials from broker
3. FIX engine library (simplefix, quickfix)

### Installation

```bash
pip install simplefix
# or
pip install quickfix
```

### Broker Setup Steps

1. **Contact your broker** to enable FIX API access
2. **Obtain FIX credentials**:
   - SenderCompID
   - TargetCompID
   - Username/Password
   - FIX server address and port
   - FIX version (typically 4.2 or 4.4)

3. **Configure firewall** to allow FIX port (usually 5201 or similar)

### Pros
- Professional-grade protocol
- Very reliable
- Widely supported by major brokers
- Direct market access
- Low latency

### Cons
- Requires broker approval
- More complex implementation
- May have additional fees
- Requires FIX protocol knowledge

### Implementation Status
See `src/connectors/mt4_connector_v2_fix.py` for FIX API implementation.

### Supported Brokers (Examples)
- IC Markets (FIX 4.4)
- FXCM (FIX 4.4)
- OANDA (FIX 4.4)
- Interactive Brokers (FIX 4.2)
- Many institutional brokers

---

## Approach 3: Bridge Solution (MQL4 + HTTP)

### Overview
Create a bridge using MQL4 Expert Advisor that runs inside MT4 and communicates with Python via HTTP REST API.

### Architecture

```
Python Application <--HTTP--> MQL4 EA (inside MT4) <---> MT4 Platform
```

### Components

1. **MQL4 Expert Advisor** - Runs in MT4, exposes HTTP server
2. **Python Connector** - Makes HTTP requests to EA
3. **Communication Protocol** - JSON over HTTP

### Installation Steps

#### Step 1: Install MQL4 Expert Advisor

1. Copy `mql4/mt4_bridge_server.mq4` to MT4's Experts folder:
   - Mac: `~/Library/Application Support/MetaTrader 4/MQL4/Experts/`
   - Windows: `C:\Program Files\MetaTrader 4\MQL4\Experts\`

2. Compile the EA in MetaEditor (F7)

3. Restart MT4

4. Drag the EA onto a chart

5. In EA settings, configure:
   - Port: 8080 (or your preferred port)
   - AllowedIPs: "127.0.0.1" (localhost)
   - Enable AutoTrading (toolbar button)

#### Step 2: Configure Python Connector

The connector is already implemented in `src/connectors/mt4_connector_v3_bridge.py`.

Configuration is automatic - it uses `http://localhost:8080` by default.

### Pros
- Works with any MT4 installation
- No broker approval needed
- Full MT4 functionality access
- Complete control over implementation
- Works with demo and live accounts

### Cons
- Requires EA to be running in MT4
- MT4 must be open
- Additional maintenance (EA + connector)
- Slightly higher latency than native

### Implementation Status
See:
- `src/connectors/mt4_connector_v3_bridge.py` - Python connector
- `mql4/mt4_bridge_server.mq4` - MQL4 Expert Advisor
- `mql4/README.md` - Detailed MQL4 setup instructions

---

## Recommendation

### For Mac Users (Your Case)

**Best Option: Bridge Solution (Approach 3)**

Reasons:
1. MT4 on Mac has limitations with external APIs
2. Bridge solution is most reliable
3. Works with any broker
4. No broker approval needed
5. Full control and flexibility

### Quick Start Steps

1. Install the MQL4 EA (copy files, compile, attach to chart)
2. Ensure MT4 is running with EA active
3. Update Python code to use bridge connector
4. Test connection

See `mql4/README.md` for detailed setup instructions.

---

## Alternative: Use MT5 Instead

If your broker supports MT5, consider using MT5 instead:

**Advantages:**
- Official Python API (MetaTrader5 package)
- Better Python integration
- More modern platform
- Better performance

**MT5 Python Package:**
```bash
pip install MetaTrader5
```

The TradingMTQ system already has full MT5 support implemented.

---

## Testing Your Implementation

### Test MT4 Connection

```python
from src.services.session_manager import session_manager
from src.database.models import TradingAccount, PlatformType
from src.database.connection import get_session

# Get MT4 account
with get_session() as db:
    account = db.query(TradingAccount).filter(
        TradingAccount.platform_type == PlatformType.MT4
    ).first()

    if account:
        # Attempt connection
        success, error = await session_manager.connect_account(account, db)

        if success:
            print("MT4 connection successful!")

            # Get connector
            connector = session_manager.get_session(account.id)

            # Test account info
            info = connector.get_account_info()
            print(f"Account: {info.balance}")
        else:
            print(f"Connection failed: {error}")
```

---

## Security Considerations

### Bridge Solution Security

1. **Local-only access**: Configure EA to only accept localhost connections
2. **Authentication**: Add API key authentication to HTTP endpoints
3. **HTTPS**: For production, use HTTPS instead of HTTP
4. **Rate limiting**: Implement request rate limiting

### FIX API Security

1. **Credentials**: Store FIX credentials securely (encrypted)
2. **IP whitelist**: Configure broker's IP whitelist
3. **Certificate**: Use SSL/TLS certificates
4. **Session monitoring**: Monitor for unauthorized sessions

---

## Troubleshooting

### Bridge Solution

**EA not responding:**
- Check MT4 is running
- Verify EA is active (green indicator in top-right)
- Check AutoTrading is enabled
- Review MT4 Experts tab for errors

**Connection refused:**
- Verify port number matches (default 8080)
- Check firewall settings
- Ensure EA is attached to chart

**Orders not executing:**
- Verify AutoTrading is enabled
- Check account permissions
- Review MT4 Journal tab

### FIX API

**Authentication failed:**
- Verify credentials with broker
- Check SenderCompID/TargetCompID
- Confirm FIX version matches

**Connection timeout:**
- Check firewall rules
- Verify FIX server address/port
- Confirm broker's FIX service is active

---

## Next Steps

1. **Choose your approach** based on your needs and broker support
2. **Install required components** (packages, EA, etc.)
3. **Configure connection** with your broker credentials
4. **Test connection** with demo account first
5. **Monitor logs** for any issues

For specific implementation help, see the respective connector files in `src/connectors/`.
