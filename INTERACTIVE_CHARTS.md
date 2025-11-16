# Interactive TradingView-Style Charts

## Features

PatternTrader Pro now uses **Plotly** for interactive, professional-grade charts that match TradingView's functionality.

### Chart Capabilities

✅ **Fully Interactive**
- Zoom in/out with mouse wheel or pinch
- Pan by clicking and dragging
- Reset view with home button
- Save chart as PNG image

✅ **Complete Trade Setup Visualization**
- **Entry line** (blue dashed) - Your entry price
- **Stop Loss** (red dashed) - Risk level
- **Take Profit** (green dashed) - Target level
- **Risk:Reward ratio** displayed in info box

✅ **Technical Analysis**
- **Support levels** (green dotted) - Automatically detected price floors
- **Resistance levels** (red dotted) - Automatically detected price ceilings
- **MA20** (blue line) - 20-period moving average
- **MA50** (purple line) - 50-period moving average
- **Trend indicator** - Shows Uptrend/Downtrend/Sideways

✅ **Pattern Information Box**
- Pattern type (ICI, Momentum, Force, Revival)
- Trade direction (LONG ↗ / SHORT ↘)
- Current trend
- Entry, Stop, Target prices
- Risk and Reward in dollars
- Risk:Reward ratio

✅ **Professional Appearance**
- Dark theme matching TradingView
- Candlestick charts with volume
- Clean, uncluttered interface
- Mobile-responsive

## How It Works

### 1. Chart Generation

When a pattern is detected, the system:

```python
from interactive_charts import draw_interactive_chart

chart_path = draw_interactive_chart(
    symbol='BTC-USD',
    timeframe='1d',
    setup={
        'entry': 45000.0,
        'stop': 44000.0,
        'target': 48000.0,
        'risk_reward': 3.0
    },
    pattern_type='ICI'
)
```

### 2. Technical Analysis

Charts automatically include:

**Support/Resistance Detection**
- Scans 20-period lookback window
- Identifies pivot highs and lows
- Shows top 3 most significant levels

**Trend Analysis**
- Compares MA20 vs MA50
- Price above both MAs = Uptrend ✅
- Price below both MAs = Downtrend ⚠️
- Mixed = Sideways ➡️

### 3. Dashboard Integration

Charts display inline in dashboard:
- HTML iframes for Plotly charts
- Full interactivity preserved
- 800px height for optimal viewing

## Usage

### Generate Test Charts

```bash
python3 historical_scanner.py
```

This creates 3 dummy test patterns with interactive charts.

### View in Dashboard

1. Visit: https://pattern-trader-pro.onrender.com
2. Scroll to "Trade Signals" section
3. Each signal shows interactive chart
4. Click and drag to pan
5. Scroll to zoom
6. Hover for exact prices

### Manual Scan

Click "🔍 Scan Now" button to trigger immediate market scan.
New patterns will appear with charts within seconds.

## Chart Controls

**Mouse Actions:**
- **Drag** - Pan the chart
- **Scroll** - Zoom in/out
- **Double-click** - Reset zoom

**Toolbar (top-right):**
- 📷 Download as PNG
- 🔍 Zoom tools
- ↔️ Pan mode
- 🏠 Reset view
- 📊 Autoscale

## Technical Details

### Libraries
- **Plotly 5.18.0** - Interactive charting
- **yfinance** - Market data
- **pandas** - Data processing
- **numpy** - Calculations

### Chart Files
- Saved as `.html` files in `static/charts/`
- ~3.5MB per chart (includes Plotly.js)
- Self-contained (no external dependencies)
- Can be opened directly in browser

### Performance
- Charts load instantly
- No server-side rendering needed
- Client-side interactivity
- Works on mobile devices

## Examples

### ICI Pattern - Bitcoin
- **Entry:** $45,000
- **Stop:** $44,000
- **Target:** $48,000
- **R:R:** 1:3
- Shows support at $43,500
- Resistance at $47,200
- Uptrend confirmed by MAs

### Momentum Pattern - S&P 500
- **Entry:** $450
- **Stop:** $448
- **Target:** $456
- **R:R:** 1:3
- Hourly timeframe
- Volume confirmation

### Force Pattern - Gold
- **Entry:** $185
- **Stop:** $183
- **Target:** $191
- **R:R:** 1:3
- Daily timeframe
- Support zone visible

## Customization

Edit `interactive_charts.py` to customize:
- Colors and styling
- Indicator periods (MA20, MA50)
- Support/Resistance sensitivity
- Chart dimensions
- Annotation positions

## Benefits vs Static Charts

| Feature | Static (matplotlib) | Interactive (Plotly) |
|---------|-------------------|---------------------|
| Zoom | ❌ | ✅ |
| Pan | ❌ | ✅ |
| Hover data | ❌ | ✅ |
| Save image | ❌ | ✅ |
| Mobile friendly | ⚠️ | ✅ |
| TradingView-like | ❌ | ✅ |
| File size | 58KB | 3.5MB |

## Future Enhancements

Potential additions:
- RSI indicator
- MACD histogram
- Fibonacci retracements
- Drawing tools
- Pattern recognition overlays
- Multi-timeframe analysis
