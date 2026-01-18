# Venice AI Arbitrage Monitor

**Automated monitoring and alerting system for VVV/DIEM token arbitrage opportunities**

## Features

- 🔍 **Real-time Price Tracking**: VVV and DIEM prices across multiple exchanges
- 📊 **Spread Monitoring**: Live mint cost vs market price analysis
- 🎯 **Arbitrage Detection**: Cross-exchange price discrepancies and mint/sell opportunities
- 💰 **VVV Buy Signals**: Technical analysis and valuation-based buy alerts
- 🔔 **Smart Notifications**: Integration with Caelum notification system
- 📈 **Historical Tracking**: Price history and pattern recognition

## How It Works

### DIEM Arbitrage Monitoring

1. **Mint Cost Calculation**: `Current Mint Rate (sVVV per DIEM) × VVV Price`
2. **Market Price Tracking**: DIEM prices on Aerodrome, CoinMarketCap, and other exchanges
3. **Spread Analysis**:
   - **Positive Spread**: Market Price > Mint Cost → Mint & Sell opportunity
   - **Negative Spread**: Market Price < Mint Cost → Hold VVV
4. **Intrinsic Value**: DCF model based on $1/day perpetual API credit (~$365 at 25% discount rate)

### VVV Buy Signal Analysis

- **Technical Indicators**: RSI, MACD, volume analysis
- **On-chain Metrics**: Staking rates, DIEM mint activity, holder distribution
- **Sentiment Analysis**: Social media and news sentiment
- **Valuation Models**: Comparison to historical price ranges and fundamentals

## Quick Start

```bash
# Clone repository
git clone https://github.com/swdatasci/venice-arbitrage-monitor.git
cd venice-arbitrage-monitor

# Install dependencies
uv pip install -r requirements.txt

# Configure settings
cp config.example.yaml config.yaml
# Edit config.yaml with your settings

# Run monitoring service
uv run python -m venice_monitor.main

# Or run as systemd service
sudo cp systemd/venice-monitor.service /etc/systemd/system/
sudo systemctl enable venice-monitor
sudo systemctl start venice-monitor
```

## Configuration

```yaml
# config.yaml
monitoring:
  check_interval_seconds: 300  # 5 minutes

  # Price sources
  vvv_sources:
    - coinmarketcap
    - coingecko
    - aerodrome

  diem_sources:
    - aerodrome
    - coinmarketcap
    - uniswap

  # Alert thresholds
  diem_arbitrage:
    min_profit_percent: 5.0      # Alert when spread > 5%
    intrinsic_value_discount: 10.0  # Alert when DIEM < $328.50 (10% below $365)

  vvv_buy_signals:
    rsi_oversold: 30             # RSI below 30 = oversold
    price_drop_percent: 15.0     # Alert on 15% drop from recent high
    volume_spike_multiplier: 2.0 # Alert when volume > 2x average

notifications:
  caelum:
    enabled: true
    host: 10.32.3.27
    port: 8090

  email:
    enabled: false
    smtp_host: smtp.gmail.com
    smtp_port: 587

  discord:
    enabled: false
    webhook_url: ""

web3:
  base_rpc_url: "https://mainnet.base.org"
  aerodrome_router: "0xBE6D8f0d05cC4be24d5167a3eF062215bE6D18a5"
```

## Architecture

```
venice-arbitrage-monitor/
├── venice_monitor/
│   ├── __init__.py
│   ├── main.py                 # Main monitoring loop
│   ├── pricing/
│   │   ├── vvv_tracker.py      # VVV price aggregation
│   │   ├── diem_tracker.py     # DIEM price aggregation
│   │   ├── mint_calculator.py  # Mint cost calculation
│   │   └── exchanges/
│   │       ├── aerodrome.py
│   │       ├── coinmarketcap.py
│   │       └── coingecko.py
│   ├── analysis/
│   │   ├── spread_analyzer.py  # Arbitrage spread detection
│   │   ├── vvv_signals.py      # VVV buy signal generation
│   │   └── intrinsic_value.py  # DCF valuation models
│   ├── notifications/
│   │   ├── caelum_notifier.py  # Caelum MCP integration
│   │   ├── email_notifier.py
│   │   └── discord_notifier.py
│   ├── storage/
│   │   ├── price_history.py    # SQLite price history
│   │   └── alert_log.py        # Alert history
│   └── utils/
│       ├── config.py
│       └── logger.py
├── tests/
├── scripts/
│   ├── backtest.py             # Backtest signals against historical data
│   └── manual_check.py         # One-time manual price check
├── systemd/
│   └── venice-monitor.service
├── config.example.yaml
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Example Alerts

### DIEM Arbitrage Opportunity
```
🎯 DIEM ARBITRAGE OPPORTUNITY DETECTED
Mint Cost: $875.50
Market Price: $945.20 (Aerodrome)
Spread: +7.96% (+$69.70 per DIEM)
Recommendation: MINT & SELL
Estimated Profit: $69.70 per DIEM (minus gas)
```

### VVV Buy Signal
```
💰 VVV BUY SIGNAL TRIGGERED
Current Price: $2.45 (-18% from 7-day high)
RSI: 28 (oversold)
24h Volume: +215% (spike detected)
On-chain: Staking rate increased 5.2%
Recommendation: STRONG BUY
```

### DIEM Undervaluation Alert
```
📉 DIEM TRADING BELOW INTRINSIC VALUE
Market Price: $312.00
Intrinsic Value: $365.00 (25% discount rate)
Discount: 14.5%
Recommendation: BUY DIEM (better than minting)
Payback Period: 312 days of $1/day API usage
```

## Integration with Caelum

The monitor integrates with your existing Caelum infrastructure:

```python
# Automatically uses Caelum MCP notification service
from venice_monitor.notifications import send_alert

send_alert(
    title="VVV Buy Signal",
    message="Price dropped 15%, RSI oversold",
    priority="high",
    device="mobile"  # Sends to your phone via Caelum
)
```

## Development

```bash
# Run tests
uv run pytest

# Backtest signals
uv run python scripts/backtest.py --start-date 2025-08-01 --end-date 2026-01-18

# Manual price check
uv run python scripts/manual_check.py
```

## License

MIT

## Author

Roderick Ford (@swdatasci)
