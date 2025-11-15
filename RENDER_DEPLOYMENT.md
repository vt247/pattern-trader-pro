# Render Deployment Guide

## Architecture

PatternTrader Pro runs on Render with:

1. **PostgreSQL Database** (Starter plan) - Stores all trade signals and account state
2. **Web Dyno** - Flask dashboard showing signals and charts
3. **Worker Dyno** - Scanner bot running hourly scans

## How It Works

### Scanner Worker
- Runs `auto_scanner_bot.py` continuously
- Scans Bitcoin, S&P 500, Gold every hour
- Finds ICI, Momentum, Force, Revival patterns
- Draws chart for each setup
- Saves to PostgreSQL database

### Web Dashboard
- Runs `web_dashboard_live.py`
- Reads signals from PostgreSQL
- Shows live account balance, open positions, trade history
- Displays charts for each setup
- Auto-refreshes every 10 seconds

### PostgreSQL Database
Stores:
- `signals` table: All trade setups with entry/stop/target/status
- `account_state` table: Current balance and equity

## Deployment Steps

Render will automatically:

1. **Create PostgreSQL database** from render.yaml
2. **Set DATABASE_URL** environment variable
3. **Build both web and worker** with Python 3.11
4. **Install dependencies** from requirements.txt
5. **Start both services**

## Monitoring

- **Web**: https://pattern-trader-pro.onrender.com
- **Worker logs**: Render Dashboard → pattern-trader-pro-scanner → Logs
- **Database**: Render Dashboard → pattern-trader-db

## Local Development

Without DATABASE_URL, the system falls back to JSON files:
- `trade_signals.json` - Trade signals
- `account_state.json` - Account state
- `static/charts/` - Chart images

Run locally:
```bash
pip install -r requirements.txt
python auto_scanner_bot.py  # Scanner
python web_dashboard_live.py  # Dashboard (separate terminal)
```

## Cost

With Render paid plan:
- PostgreSQL Starter: ~$7/month
- Web Dyno Starter: ~$7/month
- Worker Dyno Starter: ~$7/month
- **Total: ~$21/month**

## Notes

- Scanner runs 24/7 and scans every hour
- Charts saved to `/tmp` on Render (ephemeral)
- Database persists all signal data
- Initial balance: $1,000 (configurable in auto_scanner_bot.py)
