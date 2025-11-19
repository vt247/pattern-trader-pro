"""
Interactive Chart Generator with Plotly
Creates zoomable, draggable TradingView-style charts with pattern annotations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import requests


def fetch_stock_data(symbol: str, period: str, interval: str):
    """
    Fetch stock data with fallback options.
    First tries yfinance, then falls back to Alpha Vantage.
    """
    # Try yfinance first
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if not df.empty:
            # Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            return df
    except Exception as e:
        print(f"yfinance failed: {e}")

    # Fallback to Alpha Vantage (free tier)
    try:
        # Use demo key or get from environment
        api_key = os.environ.get('ALPHA_VANTAGE_KEY', 'demo')

        # Check if it's a crypto symbol (contains -USD, -EUR, etc.)
        is_crypto = '-' in symbol and any(currency in symbol for currency in ['USD', 'EUR', 'GBP', 'JPY'])

        if is_crypto:
            # Extract crypto symbol (e.g., BTC from BTC-USD)
            crypto_symbol = symbol.split('-')[0]
            market = symbol.split('-')[1] if len(symbol.split('-')) > 1 else 'USD'
            function = 'DIGITAL_CURRENCY_DAILY'
            url = f'https://www.alphavantage.co/query?function={function}&symbol={crypto_symbol}&market={market}&apikey={api_key}'
        elif interval in ['1h', '60m']:
            function = 'TIME_SERIES_INTRADAY'
            url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval=60min&outputsize=full&apikey={api_key}'
        else:
            function = 'TIME_SERIES_DAILY'
            url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&outputsize=full&apikey={api_key}'

        response = requests.get(url, timeout=10)
        data = response.json()

        # Parse Alpha Vantage response based on type
        if is_crypto:
            time_series_key = 'Time Series (Digital Currency Daily)'
        elif interval in ['1h', '60m']:
            time_series_key = 'Time Series (60min)'
        else:
            time_series_key = 'Time Series (Daily)'

        if time_series_key not in data:
            print(f"Alpha Vantage error: {data.get('Note', data.get('Error Message', 'Unknown error'))}")
            return pd.DataFrame()

        time_series = data[time_series_key]

        # Convert to DataFrame
        records = []
        for date_str, values in time_series.items():
            if is_crypto:
                # Crypto uses different field names
                records.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values['1a. open (USD)']),
                    'High': float(values['2a. high (USD)']),
                    'Low': float(values['3a. low (USD)']),
                    'Close': float(values['4a. close (USD)']),
                    'Volume': float(values.get('5. volume', 0))
                })
            else:
                records.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values['1. open']),
                    'High': float(values['2. high']),
                    'Low': float(values['3. low']),
                    'Close': float(values['4. close']),
                    'Volume': int(values['5. volume'])
                })

        df = pd.DataFrame(records)
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)

        # Filter based on period
        if 'd' in period:
            days = int(period.replace('d', ''))
            start_date = datetime.now() - timedelta(days=days)
            df = df[df.index >= start_date]

        return df

    except Exception as e:
        print(f"Alpha Vantage failed: {e}")
        return pd.DataFrame()


def check_trade_outcome(df, entry, stop, target, trade_start_time):
    """
    Check if SL or TP was hit after trade start
    Returns: (outcome, hit_price, hit_time, hit_index)
    outcome: 'sl_hit', 'tp_hit', 'open', or None
    """
    is_long = target > entry

    # Get data after trade start
    if trade_start_time:
        try:
            # Find the index of trade start or first index after it
            mask = df.index >= trade_start_time
            if not mask.any():
                return 'open', None, None, None
            post_trade_df = df[mask]
        except:
            post_trade_df = df
    else:
        post_trade_df = df

    if post_trade_df.empty:
        return 'open', None, None, None

    for idx, row in post_trade_df.iterrows():
        if is_long:
            # Long trade: check if low hit stop or high hit target
            if row['Low'] <= stop:
                return 'sl_hit', stop, idx, df.index.get_loc(idx)
            if row['High'] >= target:
                return 'tp_hit', target, idx, df.index.get_loc(idx)
        else:
            # Short trade: check if high hit stop or low hit target
            if row['High'] >= stop:
                return 'sl_hit', stop, idx, df.index.get_loc(idx)
            if row['Low'] <= target:
                return 'tp_hit', target, idx, df.index.get_loc(idx)

    return 'open', None, None, None


def calculate_support_resistance(df, lookback=20):
    """Calculate support and resistance levels"""
    highs = df['High'].rolling(window=lookback, center=True).max()
    lows = df['Low'].rolling(window=lookback, center=True).min()

    # Find pivot points
    resistance_levels = []
    support_levels = []

    for i in range(lookback, len(df) - lookback):
        if df['High'].iloc[i] == highs.iloc[i]:
            resistance_levels.append(df['High'].iloc[i])
        if df['Low'].iloc[i] == lows.iloc[i]:
            support_levels.append(df['Low'].iloc[i])

    # Get most significant levels (top 3)
    resistance = sorted(set(resistance_levels), reverse=True)[:3]
    support = sorted(set(support_levels))[:3]

    return support, resistance


def calculate_trend(df, period=20):
    """Calculate trend direction using moving averages"""
    df['MA20'] = df['Close'].rolling(window=period).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean() if len(df) >= 50 else df['Close'].rolling(window=period).mean()

    # Determine trend
    current_close = df['Close'].iloc[-1]
    ma20 = df['MA20'].iloc[-1]
    ma50 = df['MA50'].iloc[-1]

    if current_close > ma20 > ma50:
        trend = 'Uptrend'
        trend_color = 'green'
    elif current_close < ma20 < ma50:
        trend = 'Downtrend'
        trend_color = 'red'
    else:
        trend = 'Sideways'
        trend_color = 'orange'

    return trend, trend_color, df


def generate_trade_rationale(pattern_type, is_long, trend, support_levels,
                             resistance_levels, current_price, entry, stop, target):
    """Generate human-readable trade rationale"""

    # Pattern-specific rationales
    pattern_reasons = {
        'ICI': f"Institutional Candle with Imbalance detected. Large candle shows institutional activity, "
               f"followed by price imbalance creating entry opportunity.",
        'Momentum': f"Strong momentum pattern identified. Price showing clear directional movement "
                    f"with potential for continuation after retracement.",
        'Force': f"Force pattern detected. Stop hunt followed by sharp reversal indicates institutional "
                 f"accumulation/distribution and potential trend change.",
        'Revival': f"Revival setup found. Price breaking out of consolidation with increased volume, "
                   f"suggesting new trend beginning."
    }

    base_reason = pattern_reasons.get(pattern_type, f"{pattern_type} pattern identified")

    # Add trend context
    if is_long and trend == 'Uptrend':
        trend_context = "Trade aligns with uptrend (price above MA20 and MA50)"
    elif not is_long and trend == 'Downtrend':
        trend_context = "Trade aligns with downtrend (price below MA20 and MA50)"
    elif trend == 'Sideways':
        trend_context = "Range-bound market - trading breakout from consolidation"
    else:
        trend_context = "Counter-trend trade - expecting reversal"

    # Add support/resistance context
    sr_context = ""
    if is_long and support_levels:
        closest_support = min(support_levels, key=lambda x: abs(x - entry))
        if abs(closest_support - entry) / entry < 0.02:  # Within 2%
            sr_context = f"Entry near support level at ${closest_support:.2f}"
    elif not is_long and resistance_levels:
        closest_resistance = min(resistance_levels, key=lambda x: abs(x - entry))
        if abs(closest_resistance - entry) / entry < 0.02:  # Within 2%
            sr_context = f"Entry near resistance level at ${closest_resistance:.2f}"

    # Combine all context
    rationale_parts = [base_reason, trend_context]
    if sr_context:
        rationale_parts.append(sr_context)

    return ". ".join(rationale_parts) + "."


def draw_interactive_chart(symbol: str, timeframe: str, setup: dict,
                          pattern_type: str, charts_dir: str = 'static/charts'):
    """
    Draw interactive Plotly chart with all setup details
    Returns: (chart_path, trade_rationale) tuple
    """
    try:
        # Get data
        period = '90d' if timeframe == '1d' else '7d'
        df = yf.download(symbol, period=period, interval=timeframe, progress=False)

        if df.empty:
            return '', ''

        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # Use current price for realistic entry/stop/target
        current_price = df['Close'].iloc[-1]

        # Override dummy prices with realistic ones based on current price
        # Check if prices are dummy or unrealistic (>10% away from current)
        if setup.get('entry', 0) == 0 or abs(setup.get('entry', 0) - current_price) / current_price > 0.1:
            # If entry is dummy or too far from current price, recalculate
            is_long = setup.get('entry', current_price) < setup.get('target', current_price * 1.1)

            if is_long:
                # Long setup: entry near current, stop below, target above
                entry = current_price * 0.998  # Entry slightly below current
                stop = current_price * 0.975   # 2.5% stop loss
                target = current_price * 1.075  # 7.5% target (3R)
            else:
                # Short setup: entry near current, stop above, target below
                entry = current_price * 1.002  # Entry slightly above current
                stop = current_price * 1.025   # 2.5% stop loss
                target = current_price * 0.925  # 7.5% target (3R)

            setup['entry'] = entry
            setup['stop'] = stop
            setup['target'] = target
            setup['risk_reward'] = abs(target - entry) / abs(entry - stop)

        # Calculate indicators
        support_levels, resistance_levels = calculate_support_resistance(df)
        trend, trend_color, df = calculate_trend(df)

        # Create subplot with price and volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{pattern_type} Setup - {symbol} ({timeframe})', 'Volume')
        )

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price',
                increasing_line_color='green',
                decreasing_line_color='red'
            ),
            row=1, col=1
        )

        # Add Moving Averages
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MA20'],
                name='MA20',
                line=dict(color='blue', width=1),
                opacity=0.7
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MA50'],
                name='MA50',
                line=dict(color='purple', width=1),
                opacity=0.7
            ),
            row=1, col=1
        )

        # Get entry, stop, target
        entry = setup.get('entry', 0)
        stop = setup.get('stop', 0)
        target = setup.get('target', 0)
        risk_reward = setup.get('risk_reward', 0)
        is_long = target > entry

        # Add TradingView-style position area (shaded regions)
        # Start from current candle (last index) and extend to the right
        current_time = df.index[-1]

        # Calculate future time extension (20% of chart width to the right)
        from datetime import timedelta
        time_range = df.index[-1] - df.index[0]

        # Convert to timedelta for proper addition
        if hasattr(time_range, 'days'):
            # Already a timedelta
            future_time = current_time + (time_range * 0.2)
        else:
            # Convert to days and create timedelta
            days = (df.index[-1] - df.index[0]).days
            future_time = current_time + timedelta(days=int(days * 0.2))

        # Risk zone (Entry to Stop) - Red/transparent
        # Only show from current candle forward
        fig.add_shape(
            type="rect",
            x0=current_time,
            x1=future_time,
            y0=min(entry, stop),
            y1=max(entry, stop),
            fillcolor="rgba(255, 0, 0, 0.2)",
            line=dict(width=0),
            layer="below",
            row=1, col=1
        )

        # Reward zone (Entry to Target) - Green/transparent
        # Only show from current candle forward
        fig.add_shape(
            type="rect",
            x0=current_time,
            x1=future_time,
            y0=min(entry, target),
            y1=max(entry, target),
            fillcolor="rgba(0, 255, 0, 0.2)",
            line=dict(width=0),
            layer="below",
            row=1, col=1
        )

        # Add vertical line at trade start (current candle) using add_shape
        # Get y-axis range for the line
        y_min = df['Low'].min()
        y_max = df['High'].max()

        fig.add_shape(
            type="line",
            x0=current_time,
            x1=current_time,
            y0=y_min,
            y1=y_max,
            line=dict(
                color="rgba(255, 255, 255, 0.5)",
                width=2,
                dash="dot"
            ),
            row=1, col=1
        )

        # Add annotation for trade start
        fig.add_annotation(
            x=current_time,
            y=y_max,
            text="Trade Start",
            showarrow=False,
            font=dict(size=10, color="white"),
            xshift=5,
            yshift=10,
            row=1, col=1
        )

        # Add Entry line (solid, thicker)
        fig.add_hline(
            y=entry,
            line_dash="solid",
            line_color="white",
            line_width=3,
            annotation_text=f"<b>Entry: ${entry:.2f}</b>",
            annotation_position="right",
            annotation_font=dict(size=12, color="white", family="Arial Black"),
            row=1, col=1
        )

        # Add Stop Loss line
        fig.add_hline(
            y=stop,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text=f"Stop Loss: ${stop:.2f}",
            annotation_position="right",
            annotation_font=dict(size=11, color="red"),
            row=1, col=1
        )

        # Add Take Profit line
        fig.add_hline(
            y=target,
            line_dash="dash",
            line_color="green",
            line_width=2,
            annotation_text=f"Take Profit: ${target:.2f}",
            annotation_position="right",
            annotation_font=dict(size=11, color="green"),
            row=1, col=1
        )

        # Add Support levels
        for level in support_levels:
            fig.add_hline(
                y=level,
                line_dash="dot",
                line_color="rgba(0, 255, 0, 0.3)",
                line_width=1,
                annotation_text=f"Support: ${level:.2f}",
                annotation_position="left",
                annotation_font_size=10,
                row=1, col=1
            )

        # Add Resistance levels
        for level in resistance_levels:
            fig.add_hline(
                y=level,
                line_dash="dot",
                line_color="rgba(255, 0, 0, 0.3)",
                line_width=1,
                annotation_text=f"Resistance: ${level:.2f}",
                annotation_position="left",
                annotation_font_size=10,
                row=1, col=1
            )

        # Add Volume bars
        colors = ['green' if row['Close'] >= row['Open'] else 'red'
                 for _, row in df.iterrows()]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.5
            ),
            row=2, col=1
        )

        # Add pattern info annotation with better colors
        is_long = target > entry
        direction = "LONG ↗" if is_long else "SHORT ↘"
        risk = abs(entry - stop)
        reward = abs(target - entry)

        info_text = (
            f"<b>{pattern_type} Pattern</b><br>"
            f"Direction: {direction}<br>"
            f"Trend: {trend}<br>"
            f"Entry: ${entry:.2f}<br>"
            f"Stop Loss: ${stop:.2f}<br>"
            f"Take Profit: ${target:.2f}<br>"
            f"Risk: ${risk:.2f}<br>"
            f"Reward: ${reward:.2f}<br>"
            f"R:R = 1:{risk_reward:.1f}"
        )

        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text=info_text,
            showarrow=False,
            bgcolor="rgba(30, 30, 30, 0.9)",  # Dark background
            bordercolor=trend_color,
            borderwidth=2,
            font=dict(size=11, color="white"),  # White text
            align="left",
            xanchor="left",
            yanchor="top"
        )

        # Generate trade rationale based on pattern and indicators
        rationale = generate_trade_rationale(
            pattern_type,
            is_long,
            trend,
            support_levels,
            resistance_levels,
            current_price,
            entry,
            stop,
            target
        )

        # Add trade rationale as subtitle annotation below chart
        fig.add_annotation(
            x=0.5,
            y=-0.15,
            xref="paper",
            yref="paper",
            text=f"<b>Trade Rationale:</b> {rationale}",
            showarrow=False,
            font=dict(size=12, color="white"),
            align="center",
            xanchor="center",
            yanchor="top"
        )

        # Update layout for TradingView-style appearance
        fig.update_layout(
            title=dict(
                text=f"{pattern_type} Setup - {symbol} ({timeframe}) {'LONG ↗' if is_long else 'SHORT ↘'}",
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='white')
            ),
            height=800,
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=150, t=80, b=100),  # Extra bottom margin for rationale
            dragmode='pan',  # Enable pan by default
            modebar=dict(
                bgcolor='rgba(0,0,0,0)',
                color='white',
                activecolor='lightblue'
            )
        )

        # Update xaxis for better interactivity
        fig.update_xaxes(
            fixedrange=False,  # Allow zooming
            rangeslider_visible=False
        )

        # Update yaxis for better interactivity
        fig.update_yaxes(
            fixedrange=False  # Allow zooming
        )

        # Update axes
        fig.update_xaxes(
            title_text="Date",
            row=2, col=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True
        )

        fig.update_yaxes(
            title_text="Price ($)",
            row=1, col=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True
        )

        fig.update_yaxes(
            title_text="Volume",
            row=2, col=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True
        )

        # Save as HTML
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        chart_filename = f'{pattern_type}_{symbol}_{timeframe}_{timestamp}.html'
        chart_path = os.path.join(charts_dir, chart_filename)

        # Create directory if it doesn't exist
        os.makedirs(charts_dir, exist_ok=True)

        fig.write_html(chart_path, config={
            'displayModeBar': True,
            'displaylogo': False,
            'scrollZoom': True,  # Enable scroll to zoom
            'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d'],
            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{pattern_type}_{symbol}_{timeframe}',
                'height': 1000,
                'width': 1600,
                'scale': 2
            }
        })

        return f'charts/{chart_filename}', rationale

    except Exception as e:
        print(f"Error creating interactive chart: {e}")
        import traceback
        traceback.print_exc()
        return '', ''


def generate_live_chart(symbol: str, timeframe: str, entry: float, stop: float,
                        target: float, pattern_type: str, trade_timestamp: str,
                        risk_reward: float = 3.0):
    """
    Generate a live chart with current data, showing trade progress and outcome
    Returns: HTML string for the chart
    """
    try:
        # Parse trade start time
        try:
            trade_start_time = pd.to_datetime(trade_timestamp)
        except:
            trade_start_time = None

        # Calculate how many days since trade started
        if trade_start_time:
            days_since_trade = (datetime.now() - trade_start_time.to_pydatetime().replace(tzinfo=None)).days
        else:
            days_since_trade = 7

        # Get enough data to show context before trade and all data after
        if timeframe == '1d':
            # Get 30 days before trade + all days after
            period = f'{max(30 + days_since_trade, 60)}d'
        elif timeframe == '1h':
            # For hourly, get enough hours
            period = f'{max(7 + days_since_trade, 14)}d'
        else:
            period = '30d'

        # Use fetch_stock_data with fallback
        df = fetch_stock_data(symbol, period, timeframe)

        if df.empty:
            return f'''
            <div style="padding: 40px; text-align: center; color: #ff6b6b; background: #2a2a2a; border-radius: 8px; margin: 20px;">
                <h3>⚠️ Market Data Unavailable</h3>
                <p>Unable to fetch data for {symbol}</p>
                <p style="font-size: 0.9em; color: #888;">Data providers may be temporarily unavailable. Please try again later.</p>
                <hr style="border-color: #444; margin: 20px 0;">
                <p style="color: #ccc;">
                    <strong>Trade Details:</strong><br>
                    Entry: ${entry:.2f} | Stop: ${stop:.2f} | Target: ${target:.2f}
                </p>
            </div>
            '''

        # Calculate indicators
        support_levels, resistance_levels = calculate_support_resistance(df)
        trend, trend_color, df = calculate_trend(df)

        # Check trade outcome
        outcome, hit_price, hit_time, hit_index = check_trade_outcome(
            df, entry, stop, target, trade_start_time
        )

        is_long = target > entry

        # Create subplot with price and volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{pattern_type} - {symbol} ({timeframe}) - LIVE', 'Volume')
        )

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price',
                increasing_line_color='green',
                decreasing_line_color='red'
            ),
            row=1, col=1
        )

        # Add Moving Averages
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MA20'],
                name='MA20',
                line=dict(color='blue', width=1),
                opacity=0.7
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MA50'],
                name='MA50',
                line=dict(color='purple', width=1),
                opacity=0.7
            ),
            row=1, col=1
        )

        # Get y-axis range
        y_min = df['Low'].min()
        y_max = df['High'].max()

        # Add vertical line at trade start
        if trade_start_time:
            fig.add_shape(
                type="line",
                x0=trade_start_time,
                x1=trade_start_time,
                y0=y_min,
                y1=y_max,
                line=dict(
                    color="rgba(255, 255, 0, 0.7)",
                    width=2,
                    dash="dot"
                ),
                row=1, col=1
            )

            fig.add_annotation(
                x=trade_start_time,
                y=y_max,
                text="Trade Start",
                showarrow=False,
                font=dict(size=10, color="yellow"),
                xshift=5,
                yshift=10,
                row=1, col=1
            )

        # Add Entry line
        fig.add_hline(
            y=entry,
            line_dash="solid",
            line_color="white",
            line_width=3,
            annotation_text=f"<b>Entry: ${entry:.2f}</b>",
            annotation_position="right",
            annotation_font=dict(size=12, color="white", family="Arial Black"),
            row=1, col=1
        )

        # Add Stop Loss line
        fig.add_hline(
            y=stop,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text=f"Stop Loss: ${stop:.2f}",
            annotation_position="right",
            annotation_font=dict(size=11, color="red"),
            row=1, col=1
        )

        # Add Take Profit line
        fig.add_hline(
            y=target,
            line_dash="dash",
            line_color="green",
            line_width=2,
            annotation_text=f"Take Profit: ${target:.2f}",
            annotation_position="right",
            annotation_font=dict(size=11, color="green"),
            row=1, col=1
        )

        # Add outcome marker if trade closed
        if outcome == 'tp_hit' and hit_time is not None:
            fig.add_trace(
                go.Scatter(
                    x=[hit_time],
                    y=[target],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        size=20,
                        color='lime',
                        line=dict(width=2, color='white')
                    ),
                    name='TP HIT ✓',
                    showlegend=True
                ),
                row=1, col=1
            )

            fig.add_annotation(
                x=hit_time,
                y=target,
                text="<b>✓ TP HIT!</b>",
                showarrow=True,
                arrowhead=2,
                arrowcolor='lime',
                font=dict(size=14, color="lime"),
                bgcolor="rgba(0, 255, 0, 0.3)",
                bordercolor="lime",
                yshift=30,
                row=1, col=1
            )

        elif outcome == 'sl_hit' and hit_time is not None:
            fig.add_trace(
                go.Scatter(
                    x=[hit_time],
                    y=[stop],
                    mode='markers',
                    marker=dict(
                        symbol='x',
                        size=20,
                        color='red',
                        line=dict(width=2, color='white')
                    ),
                    name='SL HIT ✗',
                    showlegend=True
                ),
                row=1, col=1
            )

            fig.add_annotation(
                x=hit_time,
                y=stop,
                text="<b>✗ SL HIT</b>",
                showarrow=True,
                arrowhead=2,
                arrowcolor='red',
                font=dict(size=14, color="red"),
                bgcolor="rgba(255, 0, 0, 0.3)",
                bordercolor="red",
                yshift=-30,
                row=1, col=1
            )

        # Add Volume bars
        colors = ['green' if row['Close'] >= row['Open'] else 'red'
                 for _, row in df.iterrows()]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.5
            ),
            row=2, col=1
        )

        # Determine outcome text and color
        current_price = df['Close'].iloc[-1]
        if outcome == 'tp_hit':
            outcome_text = f"<b>✓ WINNER</b> - TP Hit at ${target:.2f}"
            outcome_color = 'lime'
            pnl_r = risk_reward
        elif outcome == 'sl_hit':
            outcome_text = f"<b>✗ LOSER</b> - SL Hit at ${stop:.2f}"
            outcome_color = 'red'
            pnl_r = -1.0
        else:
            # Calculate unrealized P&L
            if is_long:
                unrealized = (current_price - entry) / abs(entry - stop)
            else:
                unrealized = (entry - current_price) / abs(entry - stop)
            outcome_text = f"<b>OPEN</b> - Current: ${current_price:.2f} ({unrealized:+.2f}R)"
            outcome_color = 'cyan'
            pnl_r = unrealized

        # Add pattern info annotation
        direction = "LONG ↗" if is_long else "SHORT ↘"
        risk = abs(entry - stop)
        reward = abs(target - entry)

        info_text = (
            f"<b>{pattern_type} Pattern</b><br>"
            f"Direction: {direction}<br>"
            f"Trend: {trend}<br>"
            f"Entry: ${entry:.2f}<br>"
            f"Stop Loss: ${stop:.2f}<br>"
            f"Take Profit: ${target:.2f}<br>"
            f"R:R = 1:{risk_reward:.1f}<br>"
            f"<br>"
            f"<span style='color:{outcome_color}'>{outcome_text}</span>"
        )

        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text=info_text,
            showarrow=False,
            bgcolor="rgba(30, 30, 30, 0.9)",
            bordercolor=outcome_color,
            borderwidth=2,
            font=dict(size=11, color="white"),
            align="left",
            xanchor="left",
            yanchor="top"
        )

        # Update layout
        fig.update_layout(
            title=dict(
                text=f"{pattern_type} - {symbol} ({timeframe}) - {'LONG ↗' if is_long else 'SHORT ↘'} - <span style='color:{outcome_color}'>{outcome.upper().replace('_', ' ')}</span>",
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='white')
            ),
            height=700,
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=150, t=80, b=50),
            dragmode='pan',
            modebar=dict(
                bgcolor='rgba(0,0,0,0)',
                color='white',
                activecolor='lightblue'
            )
        )

        # Update axes
        fig.update_xaxes(fixedrange=False, rangeslider_visible=False)
        fig.update_yaxes(fixedrange=False)

        fig.update_xaxes(
            title_text="Date",
            row=2, col=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True
        )

        fig.update_yaxes(
            title_text="Price ($)",
            row=1, col=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True
        )

        fig.update_yaxes(
            title_text="Volume",
            row=2, col=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True
        )

        # Return HTML string
        return fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'scrollZoom': True,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d']
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f'<p>Error generating chart: {e}</p>'


if __name__ == '__main__':
    # Test the chart
    test_setup = {
        'entry': 45000.0,
        'stop': 44000.0,
        'target': 48000.0,
        'risk_reward': 3.0
    }

    path = draw_interactive_chart('BTC-USD', '1d', test_setup, 'ICI')
    print(f"Test chart created: {path}")
