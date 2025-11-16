"""
AI-Powered Trade Analysis
Analyzes past trades and provides improvement suggestions
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
import statistics


def load_trades() -> List[Dict]:
    """Load all trade signals"""
    if os.path.exists('trade_signals.json'):
        try:
            with open('trade_signals.json', 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def analyze_trades(trades: List[Dict]) -> Dict:
    """
    Comprehensive AI analysis of trading performance
    Returns insights and suggestions
    """

    if not trades:
        return {
            'status': 'no_data',
            'message': 'No trades to analyze yet. Start trading to get AI insights!'
        }

    # Separate open and closed trades
    closed_trades = [t for t in trades if t['status'] != 'open']
    open_trades = [t for t in trades if t['status'] == 'open']

    if not closed_trades:
        return {
            'status': 'no_closed',
            'message': f'You have {len(open_trades)} open positions. Analysis will be available once trades close.',
            'open_count': len(open_trades)
        }

    # Performance metrics
    wins = [t for t in closed_trades if t.get('pnl_r', 0) > 0]
    losses = [t for t in closed_trades if t.get('pnl_r', 0) < 0]
    breakeven = [t for t in closed_trades if t.get('pnl_r', 0) == 0]

    win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0
    total_r = sum([t.get('pnl_r', 0) for t in closed_trades])
    avg_win = statistics.mean([t['pnl_r'] for t in wins]) if wins else 0
    avg_loss = statistics.mean([t['pnl_r'] for t in losses]) if losses else 0

    # Pattern analysis
    pattern_performance = {}
    for trade in closed_trades:
        pattern = trade['pattern_type']
        if pattern not in pattern_performance:
            pattern_performance[pattern] = {'wins': 0, 'losses': 0, 'total_r': 0}

        if trade.get('pnl_r', 0) > 0:
            pattern_performance[pattern]['wins'] += 1
        elif trade.get('pnl_r', 0) < 0:
            pattern_performance[pattern]['losses'] += 1
        pattern_performance[pattern]['total_r'] += trade.get('pnl_r', 0)

    # Market analysis
    market_performance = {}
    for trade in closed_trades:
        market = trade['market']
        if market not in market_performance:
            market_performance[market] = {'wins': 0, 'losses': 0, 'total_r': 0}

        if trade.get('pnl_r', 0) > 0:
            market_performance[market]['wins'] += 1
        elif trade.get('pnl_r', 0) < 0:
            market_performance[market]['losses'] += 1
        market_performance[market]['total_r'] += trade.get('pnl_r', 0)

    # Timeframe analysis
    timeframe_performance = {}
    for trade in closed_trades:
        tf = trade['timeframe']
        if tf not in timeframe_performance:
            timeframe_performance[tf] = {'wins': 0, 'losses': 0, 'total_r': 0}

        if trade.get('pnl_r', 0) > 0:
            timeframe_performance[tf]['wins'] += 1
        elif trade.get('pnl_r', 0) < 0:
            timeframe_performance[tf]['losses'] += 1
        timeframe_performance[tf]['total_r'] += trade.get('pnl_r', 0)

    # Generate AI insights
    insights = []
    suggestions = []

    # Win rate analysis
    if win_rate < 40:
        insights.append(f"⚠️ Win rate is {win_rate:.1f}% - below optimal range (40-60%)")
        suggestions.append("Consider tightening entry criteria or improving pattern selection")
    elif win_rate > 60:
        insights.append(f"✅ Excellent win rate of {win_rate:.1f}%")
        suggestions.append("Consider taking larger position sizes on high-confidence setups")
    else:
        insights.append(f"✅ Win rate {win_rate:.1f}% is in healthy range (40-60%)")

    # R-multiple analysis
    if total_r < 0:
        insights.append(f"⚠️ Total R is negative ({total_r:.2f}R) - strategy needs adjustment")
        suggestions.append("Focus on cutting losses quicker and letting winners run longer")
    elif total_r > 5:
        insights.append(f"🎯 Excellent total R of {total_r:.2f}R!")
        suggestions.append("Keep following current strategy - it's working well")
    else:
        insights.append(f"📊 Total R: {total_r:.2f}R - building consistency")

    # Risk:Reward analysis
    if avg_win > 0 and avg_loss < 0:
        rr_ratio = abs(avg_win / avg_loss)
        if rr_ratio < 1.5:
            insights.append(f"⚠️ Risk:Reward ratio {rr_ratio:.2f} is suboptimal")
            suggestions.append("Look for setups with better risk:reward ratios (aim for 2:1 or better)")
        else:
            insights.append(f"✅ Good Risk:Reward ratio of {rr_ratio:.2f}")

    # Pattern performance
    best_pattern = max(pattern_performance.items(), key=lambda x: x[1]['total_r']) if pattern_performance else None
    worst_pattern = min(pattern_performance.items(), key=lambda x: x[1]['total_r']) if pattern_performance else None

    if best_pattern:
        insights.append(f"🏆 Best pattern: {best_pattern[0]} ({best_pattern[1]['total_r']:.2f}R)")
        suggestions.append(f"Focus more on {best_pattern[0]} setups - they're your strength")

    if worst_pattern and worst_pattern[1]['total_r'] < -2:
        insights.append(f"❌ Worst pattern: {worst_pattern[0]} ({worst_pattern[1]['total_r']:.2f}R)")
        suggestions.append(f"Consider avoiding {worst_pattern[0]} patterns or refining entry criteria")

    # Market performance
    best_market = max(market_performance.items(), key=lambda x: x[1]['total_r']) if market_performance else None
    worst_market = min(market_performance.items(), key=lambda x: x[1]['total_r']) if market_performance else None

    if best_market:
        insights.append(f"📈 Best market: {best_market[0]} ({best_market[1]['total_r']:.2f}R)")

    if worst_market and worst_market[1]['total_r'] < -2:
        insights.append(f"📉 Struggling with {worst_market[0]} ({worst_market[1]['total_r']:.2f}R)")
        suggestions.append(f"Be more selective when trading {worst_market[0]}")

    # Timeframe analysis
    if len(timeframe_performance) > 1:
        best_tf = max(timeframe_performance.items(), key=lambda x: x[1]['total_r'])
        insights.append(f"⏰ Best timeframe: {best_tf[0]} ({best_tf[1]['total_r']:.2f}R)")
        suggestions.append(f"Consider focusing more on {best_tf[0]} trades")

    # Recent performance trend
    recent_trades = sorted(closed_trades, key=lambda x: x['timestamp'], reverse=True)[:10]
    if len(recent_trades) >= 5:
        recent_r = sum([t.get('pnl_r', 0) for t in recent_trades])
        if recent_r < -3:
            insights.append("⚠️ Recent performance is concerning (last 10 trades)")
            suggestions.append("Take a break and review your strategy. Consider paper trading before risking more capital")
        elif recent_r > 3:
            insights.append("🚀 Recent trades are performing well!")
            suggestions.append("You're in a good flow - stay disciplined and keep executing your edge")

    return {
        'status': 'success',
        'total_trades': len(closed_trades),
        'wins': len(wins),
        'losses': len(losses),
        'breakeven': len(breakeven),
        'win_rate': win_rate,
        'total_r': total_r,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'insights': insights,
        'suggestions': suggestions,
        'pattern_performance': pattern_performance,
        'market_performance': market_performance,
        'timeframe_performance': timeframe_performance,
        'timestamp': datetime.now().isoformat()
    }


def save_analysis(analysis: Dict):
    """Save analysis to file"""
    analyses_file = 'trade_analyses.json'

    # Load existing analyses
    analyses = []
    if os.path.exists(analyses_file):
        try:
            with open(analyses_file, 'r') as f:
                analyses = json.load(f)
        except:
            analyses = []

    # Add new analysis
    analyses.append(analysis)

    # Keep only last 20 analyses
    analyses = analyses[-20:]

    # Save
    with open(analyses_file, 'w') as f:
        json.dump(analyses, f, indent=2)


def run_analysis():
    """Run analysis and display results"""
    trades = load_trades()
    analysis = analyze_trades(trades)

    if analysis['status'] != 'success':
        print(f"\n{analysis['message']}")
        return analysis

    print(f"\n{'='*60}")
    print("AI TRADE ANALYSIS")
    print(f"{'='*60}\n")

    print(f"Total Trades: {analysis['total_trades']}")
    print(f"Wins: {analysis['wins']} | Losses: {analysis['losses']} | Breakeven: {analysis['breakeven']}")
    print(f"Win Rate: {analysis['win_rate']:.1f}%")
    print(f"Total R: {analysis['total_r']:.2f}R")
    print(f"Avg Win: {analysis['avg_win']:.2f}R | Avg Loss: {analysis['avg_loss']:.2f}R")

    print(f"\n{'='*60}")
    print("KEY INSIGHTS")
    print(f"{'='*60}\n")
    for insight in analysis['insights']:
        print(f"  {insight}")

    print(f"\n{'='*60}")
    print("IMPROVEMENT SUGGESTIONS")
    print(f"{'='*60}\n")
    for i, suggestion in enumerate(analysis['suggestions'], 1):
        print(f"  {i}. {suggestion}")

    print(f"\n{'='*60}\n")

    # Save analysis
    save_analysis(analysis)

    return analysis


if __name__ == '__main__':
    run_analysis()
