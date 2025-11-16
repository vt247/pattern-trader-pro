"""
Interactive Chart Generator with Plotly
Creates zoomable, draggable TradingView-style charts with pattern annotations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os


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


def draw_interactive_chart(symbol: str, timeframe: str, setup: dict,
                          pattern_type: str, charts_dir: str = 'static/charts') -> str:
    """
    Draw interactive Plotly chart with all setup details
    Returns: path to saved HTML file
    """
    try:
        # Get data
        period = '90d' if timeframe == '1d' else '7d'
        df = yf.download(symbol, period=period, interval=timeframe, progress=False)

        if df.empty:
            return ''

        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # Use current price for realistic entry/stop/target
        current_price = df['Close'].iloc[-1]

        # Override dummy prices with realistic ones based on current price
        if setup.get('entry', 0) == 0 or abs(setup.get('entry', 0) - current_price) / current_price > 0.5:
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

        # Add pattern info annotation
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
            bgcolor=f"rgba(255, 255, 255, 0.8)",
            bordercolor=trend_color,
            borderwidth=2,
            font=dict(size=11),
            align="left",
            xanchor="left",
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
            margin=dict(l=50, r=150, t=80, b=50),
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

        return f'charts/{chart_filename}'

    except Exception as e:
        print(f"Error creating interactive chart: {e}")
        import traceback
        traceback.print_exc()
        return ''


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
