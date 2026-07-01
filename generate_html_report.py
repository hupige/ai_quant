# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import base64
import os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

STOCK_CODE = '600519'
STOCK_NAME = '贵州茅台'
DATA_DIR = r'd:\task1\data'
REPORT_DIR = r'd:\task1\report'


def fig_to_base64(fig):
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


def generate_individual_charts(df):
    charts = {}
    date_col = '日期'
    close_col = '收盘'
    high_col = '最高'
    low_col = '最低'
    volume_col = '成交量'

    dates = df[date_col]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(dates, df[close_col], label='收盘价', color='#1E88E5', linewidth=1.2)
    if 'MA20' in df.columns:
        ax.plot(dates, df['MA20'], label='MA20', color='#FF9800', linewidth=1, alpha=0.9)
    if 'MA60' in df.columns:
        ax.plot(dates, df['MA60'], label='MA60', color='#4CAF50', linewidth=1, alpha=0.9)
    ax.fill_between(dates, df[low_col], df[high_col], alpha=0.1, color='#1E88E5')
    ax.set_title('股价走势与均线', fontsize=13, fontweight='bold', pad=12)
    ax.set_ylabel('价格 (元)', fontsize=10)
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    charts['price_trend'] = fig_to_base64(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    cumulative = (1 + df['收益率'].fillna(0)).cumprod()
    ax.plot(dates, cumulative, label='累计净值', color='#7B1FA2', linewidth=1.5)
    ax.axhline(y=1, color='#666', linestyle='--', alpha=0.6, linewidth=1)
    ax.fill_between(dates, cumulative, 1, where=cumulative >= 1, alpha=0.15, color='#4CAF50', interpolate=True)
    ax.fill_between(dates, cumulative, 1, where=cumulative < 1, alpha=0.15, color='#F44336', interpolate=True)
    ax.set_title('累计收益率曲线', fontsize=13, fontweight='bold', pad=12)
    ax.set_ylabel('累计净值', fontsize=10)
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    charts['cumulative_return'] = fig_to_base64(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    if '波动率_20日' in df.columns:
        ax.plot(dates, df['波动率_20日'] * 100, label='20日年化波动率', color='#E53935', linewidth=1.2)
    if '波动率_60日' in df.columns:
        ax.plot(dates, df['波动率_60日'] * 100, label='60日年化波动率', color='#B71C1C', linewidth=1.5, alpha=0.8)
    ax.set_title('滚动波动率走势', fontsize=13, fontweight='bold', pad=12)
    ax.set_ylabel('年化波动率 (%)', fontsize=10)
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    charts['volatility'] = fig_to_base64(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    if '回撤' in df.columns:
        dd = df['回撤'] * 100
        ax.fill_between(dates, dd, 0, color='#F44336', alpha=0.35)
        ax.plot(dates, dd, color='#D32F2F', linewidth=0.8)
        max_dd_idx = dd.idxmin()
        ax.annotate('最大回撤: {:.2f}%'.format(dd.min()),
                    xy=(dates.iloc[max_dd_idx], dd.min()),
                    xytext=(30, -30), textcoords='offset points',
                    fontsize=9, color='#D32F2F', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='#D32F2F'))
    ax.set_title('回撤曲线', fontsize=13, fontweight='bold', pad=12)
    ax.set_ylabel('回撤 (%)', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    charts['drawdown'] = fig_to_base64(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    returns = df['收益率'].dropna() * 100
    n, bins, patches = ax.hist(returns, bins=60, color='#42A5F5', edgecolor='white', alpha=0.85, density=True)
    for i, patch in enumerate(patches):
        if bins[i] < 0:
            patch.set_facecolor('#EF5350')
    mean_ret = returns.mean()
    var_95 = np.percentile(returns, 5)
    ax.axvline(x=mean_ret, color='#FF9800', linestyle='--', linewidth=1.8, label='均值: {:.2f}%'.format(mean_ret))
    ax.axvline(x=var_95, color='#9C27B0', linestyle='--', linewidth=1.8, label='VaR 95%: {:.2f}%'.format(var_95))
    ax.set_title('日收益率分布直方图', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('日收益率 (%)', fontsize=10)
    ax.set_ylabel('频率密度', fontsize=10)
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    charts['return_dist'] = fig_to_base64(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    yearly_returns = {}
    df_year = df.copy()
    df_year['year'] = df_year[date_col].dt.year
    for year, group in df_year.groupby('year'):
        if len(group) > 20:
            y_return = (group[close_col].iloc[-1] / group[close_col].iloc[0] - 1) * 100
            yearly_returns[year] = y_return
    if yearly_returns:
        years = [str(y) for y in yearly_returns.keys()]
        values = list(yearly_returns.values())
        colors = ['#66BB6A' if v >= 0 else '#EF5350' for v in values]
        bars = ax.bar(years, values, color=colors, alpha=0.9, width=0.6, edgecolor='white', linewidth=1.5)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2., val + (1 if val >= 0 else -2),
                    '{:.1f}%'.format(val), ha='center', va='bottom' if val >= 0 else 'top',
                    fontsize=10, fontweight='bold',
                    color='#2E7D32' if val >= 0 else '#C62828')
    ax.axhline(y=0, color='#333', linewidth=1)
    ax.set_title('各年度收益率对比', fontsize=13, fontweight='bold', pad=12)
    ax.set_ylabel('收益率 (%)', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    charts['yearly_return'] = fig_to_base64(fig)

    return charts


def calculate_metrics(df):
    close_col = '收盘'
    date_col = '日期'
    high_col = '最高'
    low_col = '最低'

    df = df.copy()
    df['收益率'] = df[close_col].pct_change()
    df['对数收益率'] = np.log(df[close_col] / df[close_col].shift(1))

    total_days = len(df)
    start_price = df[close_col].iloc[0]
    end_price = df[close_col].iloc[-1]
    total_return = (end_price - start_price) / start_price
    annualized_return = (1 + total_return) ** (252 / total_days) - 1

    daily_vol = df['收益率'].std()
    annualized_vol = daily_vol * np.sqrt(252)
    downside_returns = df['收益率'][df['收益率'] < 0]
    downside_vol = downside_returns.std() * np.sqrt(252)

    risk_free_rate = 0.02
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_vol if annualized_vol > 0 else 0
    sortino_ratio = (annualized_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0

    cumulative = (1 + df['收益率'].fillna(0)).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    max_dd_end_idx = drawdown.idxmin()
    max_dd_start_idx = running_max[:max_dd_end_idx].idxmax()

    var_95 = np.percentile(df['收益率'].dropna(), 5)
    var_99 = np.percentile(df['收益率'].dropna(), 1)
    cvar_95 = df['收益率'][df['收益率'] <= var_95].mean()

    positive_days = len(df[df['收益率'] > 0])
    negative_days = len(df[df['收益率'] < 0])
    flat_days = len(df[df['收益率'] == 0])
    win_rate = positive_days / (positive_days + negative_days) if (positive_days + negative_days) > 0 else 0

    avg_gain = df['收益率'][df['收益率'] > 0].mean()
    avg_loss = df['收益率'][df['收益率'] < 0].mean()
    profit_loss_ratio = abs(avg_gain / avg_loss) if avg_loss != 0 else 0

    df['MA5'] = df[close_col].rolling(5).mean()
    df['MA20'] = df[close_col].rolling(20).mean()
    df['MA60'] = df[close_col].rolling(60).mean()
    df['MA250'] = df[close_col].rolling(250).mean()
    df['波动率_20日'] = df['收益率'].rolling(20).std() * np.sqrt(252)
    df['波动率_60日'] = df['收益率'].rolling(60).std() * np.sqrt(252)
    df['回撤'] = drawdown

    metrics = {
        'total_days': total_days,
        'start_price': round(start_price, 2),
        'end_price': round(end_price, 2),
        'high_price': round(df[high_col].max(), 2),
        'low_price': round(df[low_col].min(), 2),
        'total_return': total_return,
        'annualized_return': annualized_return,
        'daily_vol': daily_vol,
        'annualized_vol': annualized_vol,
        'downside_vol': downside_vol,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'max_drawdown': max_drawdown,
        'max_dd_start': str(df[date_col].iloc[max_dd_start_idx].date()),
        'max_dd_end': str(df[date_col].iloc[max_dd_end_idx].date()),
        'var_95': var_95,
        'var_99': var_99,
        'cvar_95': cvar_95,
        'positive_days': positive_days,
        'negative_days': negative_days,
        'flat_days': flat_days,
        'win_rate': win_rate,
        'avg_gain': avg_gain,
        'avg_loss': avg_loss,
        'profit_loss_ratio': profit_loss_ratio,
    }

    return metrics, df


def get_risk_level(annualized_vol, max_drawdown):
    if annualized_vol < 0.25 and abs(max_drawdown) < 0.3:
        return '较低', '#4CAF50', '该股票波动率和回撤均处于较低水平，风险相对可控，适合稳健型投资者。'
    elif annualized_vol > 0.45 or abs(max_drawdown) > 0.5:
        return '较高', '#F44336', '该股票波动率和/或回撤较大，风险水平较高，需谨慎投资，适合风险承受能力强的投资者。'
    else:
        return '中等', '#FF9800', '该股票风险水平处于A股个股中等区间，需结合自身风险承受能力决策。'


def generate_html_report(metrics, df, charts):
    date_col = '日期'
    start_date = str(df[date_col].iloc[0].date())
    end_date = str(df[date_col].iloc[-1].date())

    risk_level, risk_color, risk_desc = get_risk_level(metrics['annualized_vol'], metrics['max_drawdown'])

    total_return_class = 'positive' if metrics['total_return'] >= 0 else 'negative'
    annual_return_class = 'positive' if metrics['annualized_return'] >= 0 else 'negative'

    sharpe_assessment = ''
    if metrics['sharpe_ratio'] > 1.5:
        sharpe_assessment = '优秀'
    elif metrics['sharpe_ratio'] > 1.0:
        sharpe_assessment = '良好'
    elif metrics['sharpe_ratio'] > 0.5:
        sharpe_assessment = '一般'
    else:
        sharpe_assessment = '偏低'

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{stock_name} ({stock_code}) 股票风险分析报告</title>
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 30px 20px;
    color: #333;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    background: #fff;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    overflow: hidden;
}}

.header {{
    background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
    color: white;
    padding: 50px 40px;
    position: relative;
    overflow: hidden;
}}

.header::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    border-radius: 50%;
}}

.header h1 {{
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 10px;
    position: relative;
}}

.header .subtitle {{
    font-size: 16px;
    opacity: 0.85;
    position: relative;
}}

.header .meta {{
    margin-top: 25px;
    display: flex;
    gap: 30px;
    flex-wrap: wrap;
    position: relative;
}}

.header .meta-item {{
    display: flex;
    flex-direction: column;
    gap: 4px;
}}

.header .meta-label {{
    font-size: 12px;
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.header .meta-value {{
    font-size: 15px;
    font-weight: 500;
}}

.summary-cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    padding: 40px;
    background: #f8f9fa;
}}

.card {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    transition: transform 0.3s, box-shadow 0.3s;
    border-left: 4px solid #1E88E5;
}}

.card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}}

.card.warning {{
    border-left-color: #FF9800;
}}

.card.danger {{
    border-left-color: #F44336;
}}

.card.success {{
    border-left-color: #4CAF50;
}}

.card.purple {{
    border-left-color: #9C27B0;
}}

.card-label {{
    font-size: 13px;
    color: #666;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.card-value {{
    font-size: 28px;
    font-weight: 700;
    color: #1a237e;
}}

.card-value.positive {{
    color: #2E7D32;
}}

.card-value.negative {{
    color: #C62828;
}}

.card-sub {{
    font-size: 12px;
    color: #999;
    margin-top: 6px;
}}

.risk-badge {{
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
    color: white;
}}

.risk-badge.low {{ background: #4CAF50; }}
.risk-badge.medium {{ background: #FF9800; }}
.risk-badge.high {{ background: #F44336; }}

.section {{
    padding: 40px;
    border-bottom: 1px solid #eee;
}}

.section:last-child {{
    border-bottom: none;
}}

.section-title {{
    font-size: 22px;
    font-weight: 700;
    color: #1a237e;
    margin-bottom: 25px;
    display: flex;
    align-items: center;
    gap: 12px;
}}

.section-title::before {{
    content: '';
    width: 5px;
    height: 24px;
    background: linear-gradient(180deg, #1a237e, #3949ab);
    border-radius: 3px;
}}

.data-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
    font-size: 14px;
}}

.data-table th,
.data-table td {{
    padding: 14px 18px;
    text-align: left;
    border-bottom: 1px solid #f0f0f0;
}}

.data-table th {{
    background: #f8f9fa;
    font-weight: 600;
    color: #555;
    font-size: 13px;
}}

.data-table tr:hover {{
    background: #fafafa;
}}

.data-table .value-col {{
    text-align: right;
    font-family: 'Consolas', monospace;
    font-weight: 600;
}}

.data-table .positive {{
    color: #2E7D32;
}}

.data-table .negative {{
    color: #C62828;
}}

.chart-container {{
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    margin-top: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    text-align: center;
}}

.chart-container img {{
    max-width: 100%;
    height: auto;
    border-radius: 8px;
}}

.two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 25px;
}}

@media (max-width: 768px) {{
    .two-col {{
        grid-template-columns: 1fr;
    }}
    .header {{
        padding: 30px 20px;
    }}
    .header h1 {{
        font-size: 24px;
    }}
    .section {{
        padding: 25px 20px;
    }}
}}

.risk-assessment {{
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    border-radius: 12px;
    padding: 30px;
    margin-top: 20px;
}}

.risk-assessment h3 {{
    font-size: 18px;
    margin-bottom: 15px;
    color: #333;
}}

.risk-assessment p {{
    line-height: 1.8;
    color: #555;
    font-size: 14px;
}}

.investment-suggestions {{
    margin-top: 20px;
    padding: 20px;
    background: #fff3e0;
    border-radius: 10px;
    border-left: 4px solid #FF9800;
}}

.investment-suggestions h4 {{
    color: #E65100;
    margin-bottom: 10px;
    font-size: 15px;
}}

.investment-suggestions ul {{
    list-style: none;
    padding: 0;
}}

.investment-suggestions li {{
    padding: 6px 0 6px 24px;
    position: relative;
    color: #555;
    font-size: 14px;
    line-height: 1.6;
}}

.investment-suggestions li::before {{
    content: '\\2713';
    position: absolute;
    left: 0;
    color: #FF9800;
    font-weight: bold;
}}

.footer {{
    background: #1a237e;
    color: rgba(255,255,255,0.7);
    text-align: center;
    padding: 25px;
    font-size: 13px;
    line-height: 1.8;
}}

.footer strong {{
    color: #fff;
}}

.stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 15px;
    margin-top: 15px;
}}

.stat-item {{
    background: #f8f9fa;
    border-radius: 10px;
    padding: 18px;
    text-align: center;
}}

.stat-item .stat-num {{
    font-size: 22px;
    font-weight: 700;
    color: #1a237e;
}}

.stat-item .stat-label {{
    font-size: 12px;
    color: #888;
    margin-top: 5px;
}}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>{stock_name} ({stock_code}) 风险分析报告</h1>
    <div class="subtitle">基于四年日交易数据的专业风险评估</div>
    <div class="meta">
        <div class="meta-item">
            <span class="meta-label">报告生成时间</span>
            <span class="meta-value">{report_time}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">数据区间</span>
            <span class="meta-value">{start_date} ~ {end_date}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">数据来源</span>
            <span class="meta-value">东方财富网 (前复权)</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">整体风险等级</span>
            <span class="meta-value"><span class="risk-badge {risk_level_class}">{risk_level}</span></span>
        </div>
    </div>
</div>

<div class="summary-cards">
    <div class="card">
        <div class="card-label">累计收益率</div>
        <div class="card-value {total_return_class}">{total_return_pct}</div>
        <div class="card-sub">四年累计表现</div>
    </div>
    <div class="card">
        <div class="card-label">年化收益率</div>
        <div class="card-value {annual_return_class}">{annual_return_pct}</div>
        <div class="card-sub">年化复合收益</div>
    </div>
    <div class="card warning">
        <div class="card-label">年化波动率</div>
        <div class="card-value">{annual_vol_pct}</div>
        <div class="card-sub">总风险水平</div>
    </div>
    <div class="card danger">
        <div class="card-label">最大回撤</div>
        <div class="card-value negative">{max_drawdown_pct}</div>
        <div class="card-sub">历史最大亏损</div>
    </div>
    <div class="card purple">
        <div class="card-label">夏普比率</div>
        <div class="card-value">{sharpe_ratio}</div>
        <div class="card-sub">风险调整收益: {sharpe_assessment}</div>
    </div>
    <div class="card success">
        <div class="card-label">胜率</div>
        <div class="card-value">{win_rate_pct}</div>
        <div class="card-sub">上涨天数占比</div>
    </div>
</div>

<div class="section">
    <div class="section-title">股价走势分析</div>
    <div class="two-col">
        <div class="chart-container">
            <img src="data:image/png;base64,{chart_price}" alt="股价走势">
        </div>
        <div class="chart-container">
            <img src="data:image/png;base64,{chart_cumulative}" alt="累计收益率">
        </div>
    </div>
    <div class="stat-grid">
        <div class="stat-item">
            <div class="stat-num">{start_price}</div>
            <div class="stat-label">起始价格 (元)</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{end_price}</div>
            <div class="stat-label">最新价格 (元)</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{high_price}</div>
            <div class="stat-label">区间最高 (元)</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{low_price}</div>
            <div class="stat-label">区间最低 (元)</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{total_days}</div>
            <div class="stat-label">总交易日</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{profit_loss_ratio}</div>
            <div class="stat-label">盈亏比</div>
        </div>
    </div>
</div>

<div class="section">
    <div class="section-title">波动率风险分析</div>
    <div class="two-col">
        <div class="chart-container">
            <img src="data:image/png;base64,{chart_volatility}" alt="滚动波动率">
        </div>
        <div class="chart-container">
            <img src="data:image/png;base64,{chart_drawdown}" alt="回撤曲线">
        </div>
    </div>
    <table class="data-table">
        <thead>
            <tr>
                <th>指标名称</th>
                <th style="text-align:right;">数值</th>
                <th>说明</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>日波动率</td>
                <td class="value-col">{daily_vol_pct}</td>
                <td>单日收益率的标准差</td>
            </tr>
            <tr>
                <td>年化波动率</td>
                <td class="value-col">{annual_vol_pct}</td>
                <td>衡量整体风险水平，A股个股通常20%-50%</td>
            </tr>
            <tr>
                <td>下行波动率</td>
                <td class="value-col negative">{downside_vol_pct}</td>
                <td>仅考虑负收益波动，更贴近实际亏损风险</td>
            </tr>
            <tr>
                <td>索提诺比率</td>
                <td class="value-col">{sortino_ratio}</td>
                <td>用下行波动率调整的收益风险比</td>
            </tr>
            <tr>
                <td>最大回撤</td>
                <td class="value-col negative">{max_drawdown_pct}</td>
                <td>历史最坏情况下的最大亏损幅度</td>
            </tr>
            <tr>
                <td>最大回撤区间</td>
                <td class="value-col" style="color:#666;">{max_dd_period}</td>
                <td>最大回撤发生的时间段</td>
            </tr>
        </tbody>
    </table>
</div>

<div class="section">
    <div class="section-title">在险价值 (VaR) 分析</div>
    <div class="chart-container">
        <img src="data:image/png;base64,{chart_dist}" alt="收益率分布" style="max-width: 700px;">
    </div>
    <table class="data-table">
        <thead>
            <tr>
                <th>指标</th>
                <th style="text-align:right;">数值</th>
                <th>解释</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>VaR (95%置信度)</td>
                <td class="value-col negative">{var_95_pct}</td>
                <td>在95%的概率下，单日最大亏损不会超过该值</td>
            </tr>
            <tr>
                <td>VaR (99%置信度)</td>
                <td class="value-col negative">{var_99_pct}</td>
                <td>在99%的概率下，单日最大亏损不会超过该值</td>
            </tr>
            <tr>
                <td>CVaR (95%置信度)</td>
                <td class="value-col negative">{cvar_95_pct}</td>
                <td>当亏损超过VaR时的平均亏损，衡量尾部风险</td>
            </tr>
        </tbody>
    </table>
</div>

<div class="section">
    <div class="section-title">涨跌分布与年度表现</div>
    <div class="two-col">
        <div>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-num" style="color:#2E7D32;">{positive_days}</div>
                    <div class="stat-label">上涨天数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num" style="color:#C62828;">{negative_days}</div>
                    <div class="stat-label">下跌天数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num" style="color:#888;">{flat_days}</div>
                    <div class="stat-label">平盘天数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num" style="color:#2E7D32;">{avg_gain_pct}</div>
                    <div class="stat-label">平均涨幅</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num" style="color:#C62828;">{avg_loss_pct}</div>
                    <div class="stat-label">平均跌幅</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num">{profit_loss_ratio}</div>
                    <div class="stat-label">盈亏比</div>
                </div>
            </div>
        </div>
        <div class="chart-container">
            <img src="data:image/png;base64,{chart_yearly}" alt="年度收益率">
        </div>
    </div>
</div>

<div class="section">
    <div class="section-title">综合风险评估与投资建议</div>
    <div class="risk-assessment">
        <h3>整体风险等级：<span class="risk-badge {risk_level_class}">{risk_level}</span></h3>
        <p>{risk_desc}</p>
    </div>
    <div class="investment-suggestions">
        <h4>投资建议</h4>
        <ul>
            {suggestions_html}
        </ul>
    </div>
</div>

<div class="footer">
    <strong>免责声明</strong><br>
    本报告基于历史数据计算，仅供参考，不构成任何投资建议。<br>
    投资有风险，入市需谨慎。过往业绩不代表未来表现。
</div>

</div>
</body>
</html>'''.format(
        stock_name=STOCK_NAME,
        stock_code=STOCK_CODE,
        report_time=datetime.now().strftime('%Y年%m月%d日 %H:%M'),
        start_date=start_date,
        end_date=end_date,
        risk_level=risk_level,
        risk_level_class='low' if risk_level == '较低' else ('high' if risk_level == '较高' else 'medium'),
        total_return_pct='{:.2f}%'.format(metrics['total_return'] * 100),
        annual_return_pct='{:.2f}%'.format(metrics['annualized_return'] * 100),
        annual_vol_pct='{:.2f}%'.format(metrics['annualized_vol'] * 100),
        max_drawdown_pct='{:.2f}%'.format(metrics['max_drawdown'] * 100),
        sharpe_ratio='{:.3f}'.format(metrics['sharpe_ratio']),
        sharpe_assessment=sharpe_assessment,
        win_rate_pct='{:.2f}%'.format(metrics['win_rate'] * 100),
        total_return_class=total_return_class,
        annual_return_class=annual_return_class,
        chart_price=charts['price_trend'],
        chart_cumulative=charts['cumulative_return'],
        chart_volatility=charts['volatility'],
        chart_drawdown=charts['drawdown'],
        chart_dist=charts['return_dist'],
        chart_yearly=charts['yearly_return'],
        start_price=metrics['start_price'],
        end_price=metrics['end_price'],
        high_price=metrics['high_price'],
        low_price=metrics['low_price'],
        total_days=metrics['total_days'],
        profit_loss_ratio='{:.2f}'.format(metrics['profit_loss_ratio']),
        daily_vol_pct='{:.4f}%'.format(metrics['daily_vol'] * 100),
        downside_vol_pct='{:.2f}%'.format(metrics['downside_vol'] * 100),
        sortino_ratio='{:.3f}'.format(metrics['sortino_ratio']),
        max_dd_period='{} ~ {}'.format(metrics['max_dd_start'], metrics['max_dd_end']),
        var_95_pct='{:.4f}%'.format(metrics['var_95'] * 100),
        var_99_pct='{:.4f}%'.format(metrics['var_99'] * 100),
        cvar_95_pct='{:.4f}%'.format(metrics['cvar_95'] * 100),
        positive_days=metrics['positive_days'],
        negative_days=metrics['negative_days'],
        flat_days=metrics['flat_days'],
        avg_gain_pct='{:.4f}%'.format(metrics['avg_gain'] * 100),
        avg_loss_pct='{:.4f}%'.format(metrics['avg_loss'] * 100),
        risk_desc=risk_desc,
        suggestions_html='\n            '.join(
            '<li>{}</li>'.format(s) for s in [
                '夏普比率为{:.3f}，风险调整后收益{}'.format(metrics['sharpe_ratio'], sharpe_assessment),
                '最大回撤达{:.2f}%，需关注回撤控制能力'.format(metrics['max_drawdown'] * 100),
                '年化波动率{:.2f}%，波动水平处于{}区间'.format(metrics['annualized_vol'] * 100, '中等' if 0.2 <= metrics['annualized_vol'] <= 0.4 else ('较高' if metrics['annualized_vol'] > 0.4 else '较低')),
                '胜率为{:.2f}%，盈亏比为{:.2f}，{}'.format(metrics['win_rate'] * 100, metrics['profit_loss_ratio'],
                    '交易质量较好' if metrics['profit_loss_ratio'] > 1 and metrics['win_rate'] > 0.5 else
                    '交易质量一般' if metrics['profit_loss_ratio'] > 1 else
                    '交易质量有待提升'),
                '建议合理控制仓位，设置止损位，做好风险管理',
            ]
        )
    )

    output_path = os.path.join(REPORT_DIR, '{}_{}_风险分析报告.html'.format(STOCK_CODE, STOCK_NAME))
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print("HTML报告已保存至: {}".format(output_path))
    return output_path


def main():
    print("=" * 60)
    print("  生成精美HTML风险分析报告")
    print("=" * 60)

    csv_path = os.path.join(DATA_DIR, '{}_{}_日线数据.csv'.format(STOCK_CODE, STOCK_NAME))

    if not os.path.exists(csv_path):
        print("错误：未找到数据文件 {}".format(csv_path))
        return

    print("\n读取数据文件...")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    print("数据加载成功，共 {} 条记录".format(len(df)))

    print("\n计算风险指标...")
    metrics, df_with_ind = calculate_metrics(df)
    print("指标计算完成")

    print("\n生成分析图表...")
    charts = generate_individual_charts(df_with_ind)
    print("图表生成完成，共 {} 张".format(len(charts)))

    print("\n生成HTML报告...")
    html_path = generate_html_report(metrics, df_with_ind, charts)

    print("\n" + "=" * 60)
    print("HTML报告生成完成！")
    print("=" * 60)
    print("  报告路径: {}".format(html_path))
    print("=" * 60)


if __name__ == '__main__':
    main()
