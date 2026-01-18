# Quick Start Guide

## Setup (5 minutes)

### 1. Clone Repository
```bash
git clone https://github.com/swdatasci/venice-arbitrage-monitor.git
cd venice-arbitrage-monitor
```

### 2. Configure Settings
```bash
# Copy example configs
cp config.example.yaml config.yaml
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required API Keys:**
- **CoinMarketCap**: Get free key at https://pro.coinmarketcap.com/signup
- **CoinGecko**: Optional (works without, but rate-limited)

**Minimal .env:**
```bash
COINMARKETCAP_API_KEY=your_key_here
CAELUM_HOST=10.32.3.27
CAELUM_PORT=8090
```

### 3. Install Dependencies
```bash
uv pip install -r requirements.txt
```

## Test It Works

### Manual Price Check
```bash
uv run python scripts/manual_check.py
```

**Expected Output:**
```
============================================================
Venice AI Manual Price Check
============================================================

Fetching prices...

📊 Current Prices:
   VVV:  $2.9700
   DIEM: $391.46
   Mint Rate: 312.50 sVVV per DIEM
   Mint Cost: $928.13

🎯 Arbitrage Analysis:
   ❌ NEGATIVE: -57.83% (-536.67 USD per DIEM)
   Recommendation: HOLD VVV

💰 Valuation Analysis:
   DCF Value (25%): $365.00
   Market Price: $391.46
   ⚠️  OVERVALUED by 7.2%
   Payback Period: 391 days ($1/day API credit)
```

## Run Continuous Monitoring

### Option 1: Foreground (for testing)
```bash
uv run python -m venice_monitor.main
```

### Option 2: Systemd Service (production)
```bash
# Install service
sudo cp systemd/venice-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable venice-monitor
sudo systemctl start venice-monitor

# Check status
sudo systemctl status venice-monitor

# View logs
sudo journalctl -u venice-monitor -f
```

## What Gets Monitored

**Every 5 minutes (configurable):**
- ✅ VVV and DIEM prices from CoinMarketCap + CoinGecko
- ✅ Current mint rate from Venice API
- ✅ Arbitrage spread calculation
- ✅ DIEM intrinsic value vs market price
- ✅ VVV buy signals (RSI, price drops, volume spikes)
- ✅ Cross-exchange arbitrage opportunities

**Alerts Sent via Caelum When:**
- DIEM mint arbitrage becomes profitable (>5% spread)
- DIEM trades significantly below intrinsic value
- VVV shows strong buy signals
- Cross-exchange price discrepancies detected

## Customize Alerts

Edit `config.yaml`:

```yaml
monitoring:
  check_interval_seconds: 300  # Check every 5 minutes

  diem_arbitrage:
    min_profit_percent: 5.0    # Alert when arbitrage > 5%
    intrinsic_value_discount_percent: 10.0  # Alert when DIEM < $328.50

  vvv_buy_signals:
    rsi_oversold: 30           # RSI < 30 = oversold
    price_drop_percent: 15.0   # Alert on 15% drops
    volume_spike_multiplier: 2.0  # 2x volume spike
```

## Data Storage

Price history saved to SQLite:
```bash
data/price_history.db
```

View history:
```bash
sqlite3 data/price_history.db "SELECT datetime(timestamp), price FROM vvv_prices ORDER BY timestamp DESC LIMIT 10;"
```

## Troubleshooting

### No prices fetched
```bash
# Check API keys
echo $COINMARKETCAP_API_KEY

# Test CoinMarketCap
curl -H "X-CMC_PRO_API_KEY: $COINMARKETCAP_API_KEY" \
  "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?id=31991"
```

### Caelum notifications not working
```bash
# Check Caelum is running
curl http://10.32.3.27:8090/health

# Or disable Caelum temporarily
# Edit config.yaml: notifications.caelum.enabled: false
```

### Service won't start
```bash
# Check logs
sudo journalctl -u venice-monitor -n 50

# Test manually
cd /home/rford/venice-arbitrage-monitor
uv run python -m venice_monitor.main
```

## Next Steps

1. **Backtest signals**: `uv run python scripts/backtest.py` (coming soon)
2. **Monitor logs**: Watch for alerts in real-time
3. **Tune thresholds**: Adjust config.yaml based on alert frequency
4. **Add integrations**: Discord, email, SMS (config.yaml)

## Support

- 📁 GitHub: https://github.com/swdatasci/venice-arbitrage-monitor
- 🐛 Issues: https://github.com/swdatasci/venice-arbitrage-monitor/issues
