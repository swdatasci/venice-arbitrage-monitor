# Setting Up Email Notifications

## Gmail SMTP Configuration

### 1. Generate Gmail App Password

**Important**: You cannot use your regular Gmail password. You must create an app-specific password.

**Steps:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication (if not already enabled)
3. Go to https://myaccount.google.com/apppasswords
4. Select app: "Mail"
5. Select device: "Other (Custom name)" → Enter "Venice Monitor"
6. Click "Generate"
7. Copy the 16-character password (no spaces)

### 2. Configure `.env` File

```bash
cd /mnt/e/Repos/swdatasci/venice-arbitrage-monitor
nano .env
```

Add these lines:
```bash
# Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAIL_FROM=your-gmail@gmail.com
EMAIL_TO=roderick@swdatasci.com
```

### 3. Enable Email in Config

```bash
nano config.yaml
```

Change:
```yaml
notifications:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_user: ""  # Will be loaded from .env
    smtp_password: ""  # Will be loaded from .env
    from_address: ""  # Will be loaded from .env
    to_addresses:
      - roderick@swdatasci.com
```

### 4. Test Email Notifications

```bash
# Restart service to pick up new config
sudo systemctl restart venice-monitor

# Check logs for email sends
sudo journalctl -u venice-monitor -f | grep -i email
```

---

## Email Alert Examples

### Arbitrage Opportunity Email
```
Subject: 🎯 DIEM Arbitrage Opportunity Detected

Spread: +7.96% (+$69.70 per DIEM)
Mint Cost: $875.50
Market Price: $945.20
Recommendation: MINT & SELL

Action Required: Profitable arbitrage window open

--
Venice AI Arbitrage Monitor
Sent: 2026-01-18 01:30:00 UTC
```

### VVV Buy Signal Email
```
Subject: 💰 VVV Strong Buy Signal

Price: $2.45 (-18% from 7-day high)
RSI: 28 (oversold)
Volume: +215% spike
Signals: PRICE_DROP, RSI_OVERSOLD, VOLUME_SPIKE
Recommendation: STRONG BUY

--
Venice AI Arbitrage Monitor
Sent: 2026-01-18 01:30:00 UTC
```

---

## Alternative: SendGrid (More Reliable)

If Gmail SMTP has issues (rate limits, spam filters), use SendGrid:

### 1. Create SendGrid Account
- Sign up at https://sendgrid.com (free tier: 100 emails/day)
- Verify sender email
- Create API key

### 2. Install SendGrid
```bash
cd /mnt/e/Repos/swdatasci/venice-arbitrage-monitor
source .venv/bin/activate
uv pip install sendgrid
```

### 3. Configure
```bash
# .env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
EMAIL_FROM=alerts@swdatasci.com
EMAIL_TO=roderick@swdatasci.com
```

---

## Troubleshooting

### Email Not Sending
```bash
# Check logs
sudo journalctl -u venice-monitor | grep -i error

# Test SMTP manually
telnet smtp.gmail.com 587
```

### Gmail Blocking
- Enable "Less secure app access" (not recommended)
- Use app-specific password (recommended)
- Check Gmail "Sent" folder for sends
- Check spam folder for receives

### Rate Limits
- Gmail free: ~500 emails/day
- SendGrid free: 100 emails/day
- Reduce alert frequency in config.yaml

---

## Next Steps

1. Generate Gmail app password
2. Add to `.env` file
3. Enable in `config.yaml`
4. Restart service: `sudo systemctl restart venice-monitor`
5. Wait for next alert (check logs)

**Once configured, you'll receive emails for all arbitrage opportunities, buy signals, and valuation alerts!**
