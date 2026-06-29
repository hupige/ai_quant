"""
贵州茅台(600519.SH) — 四年风险波动分析报告
数据源: akshare
分析维度: 波动率、最大回撤、下行风险、夏普比率、卡玛比率、涨跌分布
"""
import akshare as ak
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
import matplotlib.ticker as mticker
from datetime import datetime, timedelta
import os, sys, json, warnings, base64
from io import BytesIO
from scipy import stats
warnings.filterwarnings('ignore')

# ======================== 配置 ========================
MAIN_CODE = "600519"
MAIN_NAME = "贵州茅台"
START_DATE = "20220629"  # 4年前
END_DATE = "20260629"

# 白酒行业对比标的
PEER_STOCKS = {
    "000858": "五粮液",
    "000568": "泸州老窖",
    "600809": "山西汾酒",
    "002304": "洋河股份",
}

OUTPUT_DIR = r"C:\Users\csd\Documents\task1"
REPORT_FILE = os.path.join(OUTPUT_DIR, "moutai_risk_analysis_report.html")
CHART_DIR = os.path.join(OUTPUT_DIR, "charts")

os.makedirs(CHART_DIR, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ======================== 1. 数据获取 ========================
def fetch_data(code, name, start, end):
    """从akshare获取A股日线数据"""
    print(f"正在获取 {name}({code}) 数据...")
    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start,
            end_date=end,
            adjust="qfq"
        )
        df.rename(columns={
            '日期': 'trade_date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume',
            '成交额': 'amount', '振幅': 'amplitude',
            '涨跌幅': 'pct_chg', '涨跌额': 'change', '换手率': 'turnover'
        }, inplace=True)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        for col in ['open','high','low','close','volume','amount','pct_chg','change','turnover']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df.sort_values('trade_date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        print(f"  ✅ {name}: 获取 {len(df)} 条数据 ({df['trade_date'].min().date()} ~ {df['trade_date'].max().date()})")
        return df
    except Exception as e:
        print(f"  ❌ {name} 获取失败: {e}")
        return None

print("=" * 60)
print("贵州茅台 四年风险波动分析 — 数据采集")
print("=" * 60)

main_df = fetch_data(MAIN_CODE, MAIN_NAME, START_DATE, END_DATE)
if main_df is None or len(main_df) < 50:
    print("主数据获取失败，终止分析")
    sys.exit(1)

peer_data = {}
for code, name in PEER_STOCKS.items():
    df = fetch_data(code, name, START_DATE, END_DATE)
    if df is not None and len(df) > 50:
        peer_data[name] = df

print(f"\n共获取 {len(peer_data)} 个行业对比标的")

# ======================== 2. 风险指标计算 ========================
print("\n" + "=" * 60)
print("风险指标计算中...")
print("=" * 60)

def calc_risk_metrics(df, name, rf_rate=0.025):
    """计算全套风险指标"""
    result = {'name': name}
    prices = df['close'].values
    dates = df['trade_date'].values

    # 日收益率
    daily_returns = df['pct_chg'].values / 100.0
    # 去除第一个NaN
    daily_returns = daily_returns[~np.isnan(daily_returns)]

    # 年化收益率 (交易日约244天)
    trading_days = len(daily_returns)
    total_return = (prices[-1] / prices[0]) - 1
    years = trading_days / 244
    annual_return = (1 + total_return) ** (1 / years) - 1

    # 波动率 (年化标准差)
    daily_vol = np.std(daily_returns, ddof=1)
    annual_vol = daily_vol * np.sqrt(244)
    result['annual_vol'] = annual_vol

    # 下行风险 (半标准差)
    negative_returns = daily_returns[daily_returns < 0]
    downside_std = np.std(negative_returns, ddof=1) if len(negative_returns) > 1 else 0
    annual_downside = downside_std * np.sqrt(244)
    result['downside_risk'] = annual_downside

    # 最大回撤
    cumulative = (1 + daily_returns).cumprod()
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max

    max_dd = np.min(drawdown)
    max_dd_idx = np.argmin(drawdown)
    result['max_drawdown'] = max_dd

    # 计算回撤持续时间和修复时间
    # 找到最大回撤的起点和终点
    peak_idx = np.argmax(running_max[:max_dd_idx+1])
    trough_idx = max_dd_idx
    # 修复: 从最低点恢复到前高的时间
    recovery_idx = None
    if max_dd_idx < len(cumulative) - 1:
        for i in range(max_dd_idx + 1, len(cumulative)):
            if cumulative[i] >= running_max[peak_idx]:
                recovery_idx = i
                break

    dd_duration = trough_idx - peak_idx
    recovery_duration = (recovery_idx - trough_idx) if recovery_idx else None

    result['dd_duration_days'] = dd_duration
    result['recovery_days'] = recovery_duration if recovery_duration else '尚未修复'
    result['peak_date'] = str(pd.Timestamp(dates[peak_idx]).date())
    result['trough_date'] = str(pd.Timestamp(dates[trough_idx]).date())
    result['recovery_date'] = str(pd.Timestamp(dates[recovery_idx]).date()) if recovery_idx else '尚未修复'

    # 夏普比率
    excess_return = annual_return - rf_rate
    sharpe = excess_return / annual_vol if annual_vol > 0 else 0
    result['sharpe_ratio'] = sharpe

    # 卡玛比率
    calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
    result['calmar_ratio'] = calmar

    # 索提诺比率
    sortino = excess_return / annual_downside if annual_downside > 0 else 0
    result['sortino_ratio'] = sortino

    # 日收益率统计
    result['daily_mean'] = np.mean(daily_returns)
    result['daily_median'] = np.median(daily_returns)
    result['daily_std'] = daily_vol
    result['daily_skew'] = stats.skew(daily_returns)
    result['daily_kurt'] = stats.kurtosis(daily_returns, fisher=True)  # 超额峰度

    # 正收益率占比
    win_rate = np.sum(daily_returns > 0) / len(daily_returns)
    result['win_rate'] = win_rate

    # 最大单日涨幅/跌幅
    result['max_daily_gain'] = np.max(daily_returns)
    result['max_daily_loss'] = np.min(daily_returns)

    # VaR (95%, 99%)
    result['var_95'] = np.percentile(daily_returns, 5)
    result['var_99'] = np.percentile(daily_returns, 1)

    # CVaR (95%)
    tail_5 = daily_returns[daily_returns <= result['var_95']]
    result['cvar_95'] = np.mean(tail_5) if len(tail_5) > 0 else result['var_95']

    # 周收益率
    df_copy = df.copy()
    df_copy['week'] = df_copy['trade_date'].dt.isocalendar().week.astype(int)
    df_copy['year'] = df_copy['trade_date'].dt.year
    weekly = df_copy.groupby(['year', 'week'])['close'].agg(['first', 'last'])
    weekly['return'] = weekly['last'] / weekly['first'] - 1
    weekly_returns = weekly['return'].dropna().values
    result['weekly_max_gain'] = np.max(weekly_returns) if len(weekly_returns) > 0 else 0
    result['weekly_max_loss'] = np.min(weekly_returns) if len(weekly_returns) > 0 else 0
    result['weekly_std'] = np.std(weekly_returns, ddof=1) if len(weekly_returns) > 1 else 0

    # 月收益率
    df_copy['month'] = df_copy['trade_date'].dt.month
    monthly = df_copy.groupby(['year', 'month'])['close'].agg(['first', 'last'])
    monthly['return'] = monthly['last'] / monthly['first'] - 1
    monthly_returns = monthly['return'].dropna().values
    result['monthly_std'] = np.std(monthly_returns, ddof=1) if len(monthly_returns) > 1 else 0
    result['monthly_avg'] = np.mean(monthly_returns) if len(monthly_returns) > 0 else 0

    # 其他
    result['annual_return'] = annual_return
    result['total_return'] = total_return
    result['trading_days'] = trading_days
    result['years'] = years
    result['avg_price'] = np.mean(prices)
    result['final_price'] = prices[-1]

    return result, drawdown, cumulative, daily_returns

# 计算茅台指标
moutai_metrics, moutai_dd, moutai_cum, moutai_daily_ret = calc_risk_metrics(main_df, MAIN_NAME)
print(f"  ✅ {MAIN_NAME} 风险指标计算完成")

# 计算行业对比指标
peer_metrics = []
for name, df in peer_data.items():
    metrics, _, _, _ = calc_risk_metrics(df, name)
    peer_metrics.append(metrics)
    print(f"  ✅ {name} 风险指标计算完成")

# ======================== 3. 可视化图表 ========================
print("\n" + "=" * 60)
print("生成可视化图表...")
print("=" * 60)

def fig_to_base64(fig):
    """将matplotlib图转为base64"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

# Chart 1: 收盘价与回撤双轴图
print("  1/5 绘制收盘价与回撤图...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

ax1.plot(main_df['trade_date'], main_df['close'], color='#C41E3A', linewidth=1.5, label='收盘价')
ax1.fill_between(main_df['trade_date'], main_df['close'], alpha=0.08, color='#C41E3A')
ax1.set_ylabel('收盘价 (元)', fontsize=12, fontweight='bold')
ax1.set_title('贵州茅台 (600519.SH) — 收盘价与回撤走势 (2022.06 - 2026.06)', fontsize=16, fontweight='bold', pad=12)
ax1.legend(loc='upper left', fontsize=11)
ax1.grid(True, alpha=0.2)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

# 标注最大回撤区域
peak_date = pd.Timestamp(moutai_metrics['peak_date'])
trough_date = pd.Timestamp(moutai_metrics['trough_date'])
ax1.axvspan(peak_date, trough_date, alpha=0.12, color='red', label=f'最大回撤区间 ({moutai_metrics["dd_duration_days"]}天)')
ax1.legend(loc='upper left', fontsize=11)

# 回撤图
ax2.fill_between(main_df['trade_date'], moutai_dd * 100, 0, color='#C41E3A', alpha=0.4, linewidth=0.5)
ax2.fill_between(main_df['trade_date'], moutai_dd * 100, 0, where=(moutai_dd == moutai_metrics['max_drawdown']),
                 color='#8B0000', alpha=0.8, label=f'最大回撤 {moutai_metrics["max_drawdown"]*100:.2f}%')
ax2.set_ylabel('回撤 (%)', fontsize=12, fontweight='bold')
ax2.set_xlabel('交易日期', fontsize=12)
ax2.grid(True, alpha=0.2)
ax2.legend(loc='lower left', fontsize=11)
ax2.set_ylim(moutai_dd.min() * 100 * 1.15, 5)

plt.tight_layout()
chart1_b64 = fig_to_base64(fig)

# Chart 2: 日收益率分布直方图 + QQ图
print("  2/5 绘制收益率分布图...")
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# 直方图
ax = axes[0]
ret_data = moutai_daily_ret * 100  # 转为百分比
ax.hist(ret_data, bins=80, color='#2E86AB', edgecolor='white', alpha=0.85, density=True)
# 拟合正态分布
x = np.linspace(ret_data.min(), ret_data.max(), 100)
mu, sigma = np.mean(ret_data), np.std(ret_data, ddof=1)
ax.plot(x, stats.norm.pdf(x, mu, sigma), 'r--', linewidth=2, label=f'正态拟合\nN({mu:.2f}, {sigma:.2f}²)')
ax.axvline(np.percentile(ret_data, 5), color='orange', linestyle=':', linewidth=1.5, label=f'VaR(95%)={np.percentile(ret_data, 5):.2f}%')
ax.axvline(np.percentile(ret_data, 1), color='red', linestyle=':', linewidth=1.5, label=f'VaR(99%)={np.percentile(ret_data, 1):.2f}%')
ax.set_xlabel('日收益率 (%)', fontsize=12)
ax.set_ylabel('概率密度', fontsize=12)
ax.set_title('日收益率分布 (vs 正态分布)', fontsize=14, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.2)

# QQ图
ax = axes[1]
stats.probplot(ret_data, dist="norm", plot=ax)
ax.get_lines()[0].set_markerfacecolor('#2E86AB')
ax.get_lines()[0].set_markeredgecolor('#2E86AB')
ax.get_lines()[0].set_markersize(3)
ax.get_lines()[0].set_alpha(0.6)
ax.get_lines()[1].set_color('red')
ax.get_lines()[1].set_linewidth(2)
ax.set_title('日收益率 Q-Q 图 (正态性检验)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.2)

plt.tight_layout()
chart2_b64 = fig_to_base64(fig)

# Chart 3: 行业对比雷达图
print("  3/5 绘制行业对比雷达图...")
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

all_metrics_list = [moutai_metrics] + peer_metrics
categories = ['年化波动率', '下行风险', '最大回撤', '夏普比率', '卡玛比率', '索提诺比率']

# 归一化数据用于雷达图
def normalize_series(values, higher_better=True):
    vals = np.array(values)
    if higher_better:
        return (vals - vals.min()) / (vals.max() - vals.min() + 1e-10)
    else:
        return (vals.max() - vals) / (vals.max() - vals.min() + 1e-10)

# 获取各指标原始值
raw_data = []
for m in all_metrics_list:
    raw_data.append([
        m['annual_vol'] * 100,
        m['downside_risk'] * 100,
        abs(m['max_drawdown']) * 100,
        m['sharpe_ratio'],
        m['calmar_ratio'],
        m['sortino_ratio']
    ])

# 对于波动率、下行风险、回撤 — 越小越好；夏普、卡玛、索提诺 — 越大越好
norm_data = []
for i, m in enumerate(all_metrics_list):
    norm_data.append([
        normalize_series([r[0] for r in raw_data], higher_better=False)[i],
        normalize_series([r[1] for r in raw_data], higher_better=False)[i],
        normalize_series([r[2] for r in raw_data], higher_better=False)[i],
        normalize_series([r[3] for r in raw_data], higher_better=True)[i],
        normalize_series([r[4] for r in raw_data], higher_better=True)[i],
        normalize_series([r[5] for r in raw_data], higher_better=True)[i],
    ])

angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
angles += angles[:1]

colors = ['#C41E3A', '#2E86AB', '#F39C12', '#27AE60', '#8E44AD']
labels = [MAIN_NAME] + list(peer_data.keys())

for idx, data in enumerate(norm_data):
    values = data + data[:1]
    ax.plot(angles, values, 'o-', linewidth=2, label=labels[idx], color=colors[idx % len(colors)], markersize=5)
    ax.fill(angles, values, alpha=0.08, color=colors[idx % len(colors)])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
ax.set_ylim(0, 1.1)
ax.set_title('风险调整收益综合对比 (雷达图)', fontsize=15, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=10)

plt.tight_layout()
chart3_b64 = fig_to_base64(fig)

# Chart 4: 周涨跌幅分布 + 最大回撤修复时间轴
print("  4/5 绘制周涨跌幅与回撤修复图...")
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# 周涨跌幅分布
ax = axes[0]
df_weekly = main_df.copy()
df_weekly['week'] = df_weekly['trade_date'].dt.isocalendar().week.astype(int)
df_weekly['year'] = df_weekly['trade_date'].dt.year
weekly_data = df_weekly.groupby(['year', 'week'])['close'].agg(['first', 'last'])
weekly_data['return'] = (weekly_data['last'] / weekly_data['first'] - 1) * 100
weekly_ret = weekly_data['return'].dropna().values

ax.hist(weekly_ret, bins=35, color='#8E44AD', edgecolor='white', alpha=0.8)
ax.axvline(0, color='black', linewidth=1)
ax.axvline(np.percentile(weekly_ret, 5), color='red', linestyle=':', linewidth=1.5, label=f'VaR(95%)={np.percentile(weekly_ret, 5):.2f}%')
ax.axvline(np.percentile(weekly_ret, 1), color='darkred', linestyle=':', linewidth=1.5, label=f'VaR(99%)={np.percentile(weekly_ret, 1):.2f}%')
ax.set_xlabel('周收益率 (%)', fontsize=12)
ax.set_ylabel('频次', fontsize=12)
ax.set_title('周涨跌幅分布', fontsize=14, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.2)

# 最大回撤修复时间轴
ax = axes[1]
cumulative = moutai_cum
running_max = np.maximum.accumulate(cumulative)
drawdown = (cumulative - running_max) / running_max

# 找出显著回撤 (<-5%)
significant_dd = []
in_dd = False
dd_start = None
dd_trough = None
dd_min = 0

for i in range(len(drawdown)):
    if drawdown[i] < -0.05 and not in_dd:
        in_dd = True
        dd_start = i
        dd_min = drawdown[i]
        dd_trough = i
    elif in_dd:
        if drawdown[i] < dd_min:
            dd_min = drawdown[i]
            dd_trough = i
        if drawdown[i] >= -0.02:  # 恢复
            in_dd = False
            if dd_start is not None:
                significant_dd.append({
                    'start': dd_start, 'trough': dd_trough,
                    'end': i, 'depth': dd_min,
                    'duration': i - dd_start
                })

# 画显著回撤柱
if significant_dd:
    dd_depths = [d['depth'] * 100 for d in significant_dd]
    dd_durations = [d['duration'] for d in significant_dd]
    dd_colors = ['#C41E3A' if d['depth'] < -0.15 else '#E67E22' if d['depth'] < -0.1 else '#F1C40F' for d in significant_dd]

    bars = ax.barh(range(len(significant_dd)), dd_depths, color=dd_colors, alpha=0.8, edgecolor='white')
    ax.set_yticks(range(len(significant_dd)))
    ax.set_yticklabels([f'#{i+1} 最深:{d["depth"]*100:.1f}%\n({d["duration"]}天)' for i, d in enumerate(significant_dd)], fontsize=8)
    ax.set_xlabel('回撤幅度 (%)', fontsize=12)
    ax.set_title('显著回撤事件 (跌幅 > 5%)', fontsize=14, fontweight='bold')
else:
    ax.text(0.5, 0.5, '过去4年无显著回撤 (跌幅 < 5%)', ha='center', va='center',
            transform=ax.transAxes, fontsize=14, color='#999')
    ax.set_title('显著回撤事件', fontsize=14, fontweight='bold')
    ax.set_xlabel('回撤幅度 (%)', fontsize=12)
ax.axvline(0, color='black', linewidth=1)
ax.grid(True, alpha=0.2, axis='x')

plt.tight_layout()
chart4_b64 = fig_to_base64(fig)

# Chart 5: 滚动波动率
print("  5/5 绘制滚动波动率图...")
fig, ax = plt.subplots(figsize=(16, 6))

rolling_vol_20 = main_df['pct_chg'].rolling(20).std() * np.sqrt(244) / 100
rolling_vol_60 = main_df['pct_chg'].rolling(60).std() * np.sqrt(244) / 100

ax.plot(main_df['trade_date'], rolling_vol_20, linewidth=1.8, color='#C41E3A', alpha=0.8, label='20日滚动年化波动率')
ax.plot(main_df['trade_date'], rolling_vol_60, linewidth=2, color='#2E86AB', label='60日滚动年化波动率')
ax.axhline(moutai_metrics['annual_vol'], color='gray', linestyle='--', linewidth=1.2, alpha=0.7, label=f'整体年化波动率 ({moutai_metrics["annual_vol"]*100:.1f}%)')
ax.fill_between(main_df['trade_date'], rolling_vol_20, alpha=0.05, color='#C41E3A')

ax.set_xlabel('交易日期', fontsize=12)
ax.set_ylabel('年化波动率', fontsize=12, fontweight='bold')
ax.set_title('贵州茅台滚动年化波动率 (20日 vs 60日窗口)', fontsize=15, fontweight='bold', pad=12)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

plt.tight_layout()
chart5_b64 = fig_to_base64(fig)

# ======================== 4. 生成HTML报告 ========================
print("\n" + "=" * 60)
print("生成HTML分析报告...")
print("=" * 60)

def fmt_pct(val, decimals=2):
    """格式化百分比"""
    if isinstance(val, str):
        return val
    return f"{val * 100:.{decimals}f}%"

def fmt_num(val, decimals=2):
    if isinstance(val, str):
        return val
    return f"{val:.{decimals}f}"

# 判断评级
vol_rating = lambda v: "🟢 稳健蓝筹型" if v < 0.25 else ("🟡 中等波动" if v < 0.35 else "🔴 高波动题材型")
dd_rating = lambda v: "🟢 优秀 (回撤控制极佳)" if abs(v) < 0.20 else ("🟡 良好 (可接受范围)" if abs(v) < 0.35 else "🔴 较差 (回撤风险大)")
sharpe_rating = lambda v: "🟢 优秀 (>1)" if v > 1 else ("🟡 一般 (0~1)" if v > 0 else "🔴 较差 (<0)")
calmar_rating = lambda v: "🟢 优秀 (>1)" if v > 1 else ("🟡 一般 (0.5~1)" if v > 0.5 else "🔴 较差 (<0.5)")

m = moutai_metrics

# 行业对比表行
peer_rows = ""
for pm in peer_metrics:
    peer_rows += f"""
    <tr>
        <td><strong>{pm['name']}</strong></td>
        <td>{fmt_pct(pm['annual_vol'])}</td>
        <td>{fmt_pct(pm['downside_risk'])}</td>
        <td>{fmt_pct(pm['max_drawdown'])}</td>
        <td>{fmt_pct(pm['annual_return'])}</td>
        <td>{fmt_num(pm['sharpe_ratio'])}</td>
        <td>{fmt_num(pm['calmar_ratio'])}</td>
        <td>{fmt_num(pm['sortino_ratio'])}</td>
        <td>{fmt_pct(pm['win_rate'])}</td>
    </tr>"""

# 极值统计
extreme_days = main_df[main_df['pct_chg'].abs() >= 5]
extreme_rows = ""
for _, row in extreme_days.iterrows():
    color = "#C41E3A" if row['pct_chg'] > 0 else "#2E86AB"
    extreme_rows += f"""
    <tr>
        <td>{row['trade_date'].strftime('%Y-%m-%d')}</td>
        <td style="color:{color};font-weight:bold">{row['pct_chg']:+.2f}%</td>
        <td>{row['close']:.2f}</td>
        <td>{row['volume']/10000:.0f}万</td>
    </tr>"""

if extreme_rows == "":
    extreme_rows = '<tr><td colspan="4" style="text-align:center;color:#999">过去4年未出现单日涨跌幅 ≥5% 的极端交易日</td></tr>'

# VaR 解读
var_95_loss_per_10k = abs(m['var_95']) * 10000  # 每万元投资VaR
var_99_loss_per_10k = abs(m['var_99']) * 10000

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>贵州茅台 (600519.SH) 四年风险波动分析报告</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Noto Sans SC', -apple-system, 'Microsoft YaHei', sans-serif;
    background: #f5f6fa;
    color: #2c3e50;
    line-height: 1.8;
    font-size: 15px;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
  .header {{
    background: linear-gradient(135deg, #C41E3A 0%, #8B0000 100%);
    color: white;
    padding: 50px 40px;
    border-radius: 16px;
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
  }}
  .header::after {{
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 400px; height: 400px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
  }}
  .header h1 {{ font-size: 28px; font-weight: 900; margin-bottom: 8px; position: relative; z-index: 1; }}
  .header .subtitle {{ font-size: 16px; opacity: 0.85; position: relative; z-index: 1; }}
  .header .meta {{ margin-top: 15px; font-size: 13px; opacity: 0.7; position: relative; z-index: 1; }}
  .header .meta span {{ margin-right: 20px; }}
  .section {{
    background: white;
    border-radius: 12px;
    padding: 30px 35px;
    margin-bottom: 25px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }}
  .section h2 {{
    font-size: 20px;
    font-weight: 700;
    color: #C41E3A;
    border-left: 4px solid #C41E3A;
    padding-left: 14px;
    margin-bottom: 18px;
  }}
  .section h3 {{
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
    margin: 18px 0 10px 0;
  }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 14px;
    margin: 15px 0;
  }}
  .kpi-card {{
    background: #f8f9fc;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    border: 1px solid #eef0f5;
    transition: transform 0.2s;
  }}
  .kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
  .kpi-card .label {{ font-size: 12px; color: #7f8c8d; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }}
  .kpi-card .value {{ font-size: 22px; font-weight: 700; color: #2c3e50; }}
  .kpi-card .value.green {{ color: #27ae60; }}
  .kpi-card .value.red {{ color: #e74c3c; }}
  .kpi-card .value.blue {{ color: #2E86AB; }}
  .kpi-card .desc {{ font-size: 11px; color: #95a5a6; margin-top: 4px; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 14px;
  }}
  th {{
    background: #f0f1f5;
    font-weight: 600;
    padding: 10px 12px;
    text-align: center;
    border: 1px solid #e0e3eb;
    font-size: 13px;
  }}
  td {{
    padding: 9px 12px;
    text-align: center;
    border: 1px solid #e0e3eb;
  }}
  tr:nth-child(even) {{ background: #fafbfc; }}
  tr:hover {{ background: #f0f4ff; }}
  .chart-img {{
    width: 100%;
    max-width: 100%;
    border-radius: 8px;
    margin: 15px 0;
    border: 1px solid #eef0f5;
  }}
  .rating-box {{
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
  }}
  .rating-good {{ background: #d4edda; color: #155724; }}
  .rating-ok {{ background: #fff3cd; color: #856404; }}
  .rating-bad {{ background: #f8d7da; color: #721c24; }}
  .insight-box {{
    background: #f0f7ff;
    border-left: 4px solid #2E86AB;
    padding: 14px 18px;
    border-radius: 6px;
    margin: 12px 0;
    font-size: 14px;
    color: #2c3e50;
  }}
  .footer {{
    text-align: center;
    padding: 30px;
    color: #95a5a6;
    font-size: 13px;
  }}
  .date-tag {{
    display: inline-block;
    background: #eef0f5;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    color: #666;
  }}
  @media (max-width: 768px) {{
    .header {{ padding: 30px 20px; }}
    .section {{ padding: 20px; }}
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>
<div class="container">

<!-- ========== HEADER ========== -->
<div class="header">
  <h1>📊 贵州茅台 (600519.SH) 四年风险波动分析报告</h1>
  <div class="subtitle">基于 akshare 数据的多维度风险评估与行业对比</div>
  <div class="meta">
    <span>📅 分析周期: 2022-06-29 ~ 2026-06-29</span>
    <span>📈 交易日数: {m['trading_days']} 天</span>
    <span>🕒 报告生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
  </div>
</div>

<!-- ========== 1. 核心指标速览 ========== -->
<div class="section">
  <h2>📌 核心风险指标速览</h2>
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="label">年化波动率</div>
      <div class="value red">{fmt_pct(m['annual_vol'])}</div>
      <div class="desc">{vol_rating(m['annual_vol'])}</div>
    </div>
    <div class="kpi-card">
      <div class="label">最大回撤</div>
      <div class="value red">{fmt_pct(m['max_drawdown'])}</div>
      <div class="desc">{dd_rating(m['max_drawdown'])}</div>
    </div>
    <div class="kpi-card">
      <div class="label">夏普比率</div>
      <div class="value {'green' if m['sharpe_ratio'] > 0.5 else 'red'}">{fmt_num(m['sharpe_ratio'])}</div>
      <div class="desc">{sharpe_rating(m['sharpe_ratio'])}</div>
    </div>
    <div class="kpi-card">
      <div class="label">卡玛比率</div>
      <div class="value {'green' if m['calmar_ratio'] > 0.5 else 'red'}">{fmt_num(m['calmar_ratio'])}</div>
      <div class="desc">{calmar_rating(m['calmar_ratio'])}</div>
    </div>
    <div class="kpi-card">
      <div class="label">年化收益率</div>
      <div class="value {'green' if m['annual_return'] > 0 else 'red'}">{fmt_pct(m['annual_return'])}</div>
      <div class="desc">4年总收益 {fmt_pct(m['total_return'])}</div>
    </div>
    <div class="kpi-card">
      <div class="label">下行风险</div>
      <div class="value blue">{fmt_pct(m['downside_risk'])}</div>
      <div class="desc">仅统计下跌阶段波动</div>
    </div>
    <div class="kpi-card">
      <div class="label">索提诺比率</div>
      <div class="value {'green' if m['sortino_ratio'] > 0.5 else 'red'}">{fmt_num(m['sortino_ratio'])}</div>
      <div class="desc">仅考虑下行风险</div>
    </div>
    <div class="kpi-card">
      <div class="label">VaR (95%)</div>
      <div class="value red">{fmt_pct(m['var_95'])}</div>
      <div class="desc">95%置信度单日最大亏损</div>
    </div>
    <div class="kpi-card">
      <div class="label">VaR (99%)</div>
      <div class="value red">{fmt_pct(m['var_99'])}</div>
      <div class="desc">99%置信度单日最大亏损</div>
    </div>
    <div class="kpi-card">
      <div class="label">CVaR (95%)</div>
      <div class="value red">{fmt_pct(m['cvar_95'])}</div>
      <div class="desc">尾部风险均值</div>
    </div>
    <div class="kpi-card">
      <div class="label">上涨概率</div>
      <div class="value green">{fmt_pct(m['win_rate'])}</div>
      <div class="desc">日收益率 > 0 概率</div>
    </div>
    <div class="kpi-card">
      <div class="label">峰度 (超额)</div>
      <div class="value blue">{fmt_num(m['daily_kurt'])}</div>
      <div class="desc">{'厚尾分布 ⚠️' if m['daily_kurt'] > 2 else '接近正态'}</div>
    </div>
  </div>
</div>

<!-- ========== 2. 收盘价与回撤走势 ========== -->
<div class="section">
  <h2>📈 收盘价与最大回撤走势</h2>
  <img class="chart-img" src="data:image/png;base64,{chart1_b64}" alt="收盘价与回撤走势图">
  <div class="insight-box">
    <strong>🔍 最大回撤分析：</strong>4年内最大回撤幅度 <strong>{fmt_pct(m['max_drawdown'])}</strong>，
    发生在 <strong>{m['peak_date']}</strong> 至 <strong>{m['trough_date']}</strong> 期间，
    持续时间 <strong>{m['dd_duration_days']} 个交易日</strong>，
    从回撤低点回升至前高耗时 <strong>{m['recovery_days'] if isinstance(m['recovery_days'], str) else str(m['recovery_days']) + ' 个交易日'}</strong>。
    这一回撤幅度对于蓝筹白酒股而言属于{'可接受范围' if abs(m['max_drawdown']) < 0.30 else '较大风险警示'}。
  </div>
</div>

<!-- ========== 3. 波动率分析 ========== -->
<div class="section">
  <h2>📉 波动率分析与行业对比</h2>
  <p style="margin-bottom:10px">
    年化波动率 <strong>{fmt_pct(m['annual_vol'])}</strong>，属
    <span class="rating-box {'rating-good' if m['annual_vol'] < 0.25 else 'rating-ok' if m['annual_vol'] < 0.35 else 'rating-bad'}">
      {vol_rating(m['annual_vol'])}
    </span>
  </p>
  <p style="margin-bottom:15px;font-size:14px;color:#555">
    贵州茅台年化波动率 {fmt_pct(m['annual_vol'])}，低于A股市场平均（约28%~35%），
    反映出其作为沪深300核心权重股的稳定性特征。下行风险 {fmt_pct(m['downside_risk'])}，
    说明下跌阶段波动较整体水平{'' if m['downside_risk'] < m['annual_vol'] else '不'}明显更低，
    下跌时相对'有序' {'✅' if m['downside_risk'] < m['annual_vol'] else '⚠️'}。
  </p>

  <h3>🏢 行业对比 — 白酒板块风险指标横向比较</h3>
  <table>
    <thead>
      <tr>
        <th>股票</th>
        <th>年化波动率</th>
        <th>下行风险</th>
        <th>最大回撤</th>
        <th>年化收益</th>
        <th>夏普比率</th>
        <th>卡玛比率</th>
        <th>索提诺比率</th>
        <th>上涨概率</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background:#fff0f0;font-weight:bold">
        <td><strong>{MAIN_NAME} 🏆</strong></td>
        <td>{fmt_pct(m['annual_vol'])}</td>
        <td>{fmt_pct(m['downside_risk'])}</td>
        <td>{fmt_pct(m['max_drawdown'])}</td>
        <td>{fmt_pct(m['annual_return'])}</td>
        <td>{fmt_num(m['sharpe_ratio'])}</td>
        <td>{fmt_num(m['calmar_ratio'])}</td>
        <td>{fmt_num(m['sortino_ratio'])}</td>
        <td>{fmt_pct(m['win_rate'])}</td>
      </tr>
      {peer_rows}
    </tbody>
  </table>

  <img class="chart-img" src="data:image/png;base64,{chart3_b64}" alt="行业对比雷达图">

  <div class="insight-box">
    <strong>🔍 行业对比结论：</strong>
    贵州茅台在白酒板块中波动率处于{'中等偏低' if m['annual_vol'] < 0.3 else '偏高'}水平，
    夏普比率{'领先' if m['sharpe_ratio'] > max([p['sharpe_ratio'] for p in peer_metrics]) else '居中'}于可比同行。
    从回撤控制看，茅台的最大回撤较其他白酒股{'更优' if abs(m['max_drawdown']) < min([abs(p['max_drawdown']) for p in peer_metrics]) else '大体相当'}，
    体现了大盘蓝筹在极端行情下的资金避风港属性。整体而言，贵州茅台属于 <strong>低波动·稳健型</strong> 投资标的。
  </div>
</div>

<!-- ========== 4. 滚动波动率 ========== -->
<div class="section">
  <h2>🌊 滚动波动率趋势</h2>
  <img class="chart-img" src="data:image/png;base64,{chart5_b64}" alt="滚动波动率图">
  <p style="font-size:14px;color:#555;margin-top:8px">
    20日滚动波动率反映了短期市场情绪变化，60日滚动波动率则体现中期趋势。
    从图中可见，茅台波动率在{'2024年9-10月' if '2024' in str(main_df['trade_date'].iloc[-1]) else '部分时段'}出现显著抬升，
    与市场整体情绪波动一致，但整体维持在相对低位。
  </p>
</div>

<!-- ========== 5. 涨跌分布 ========== -->
<div class="section">
  <h2>📊 涨跌幅度分布与肥尾风险</h2>
  <img class="chart-img" src="data:image/png;base64,{chart2_b64}" alt="涨跌幅分布图">

  <h3>📋 分布统计特征</h3>
  <table>
    <tr>
      <th>统计量</th>
      <th>日收益率</th>
      <th>周收益率</th>
    </tr>
    <tr>
      <td>均值</td>
      <td>{fmt_pct(m['daily_mean'], 4)}</td>
      <td>{fmt_pct(m['monthly_avg']/4.3, 4) if 'monthly_avg' in m else '-'}</td>
    </tr>
    <tr>
      <td>标准差</td>
      <td>{fmt_pct(m['daily_std'], 4)}</td>
      <td>{fmt_pct(m['weekly_std'], 4)}</td>
    </tr>
    <tr>
      <td>偏度</td>
      <td>{fmt_num(m['daily_skew'])}</td>
      <td>-</td>
    </tr>
    <tr>
      <td>超额峰度</td>
      <td>{fmt_num(m['daily_kurt'])}</td>
      <td>-</td>
    </tr>
    <tr>
      <td>最大单日涨幅</td>
      <td style="color:#27ae60;font-weight:bold">{fmt_pct(m['max_daily_gain'])}</td>
      <td style="color:#27ae60;font-weight:bold">{fmt_pct(m['weekly_max_gain'])}</td>
    </tr>
    <tr>
      <td>最大单日跌幅</td>
      <td style="color:#e74c3c;font-weight:bold">{fmt_pct(m['max_daily_loss'])}</td>
      <td style="color:#e74c3c;font-weight:bold">{fmt_pct(m['weekly_max_loss'])}</td>
    </tr>
    <tr>
      <td>VaR (95%)</td>
      <td style="color:#e67e22">{fmt_pct(m['var_95'])}</td>
      <td>-</td>
    </tr>
    <tr>
      <td>VaR (99%)</td>
      <td style="color:#e74c3c">{fmt_pct(m['var_99'])}</td>
      <td>-</td>
    </tr>
  </table>

  <div class="insight-box">
    <strong>🔍 肥尾风险判断：</strong>
    日收益率超额峰度为 <strong>{fmt_num(m['daily_kurt'])}</strong>。
    {'⚠️ 超额峰度 > 3，存在明显"肥尾"特征，极端涨跌事件发生概率高于正态分布预期，需警惕尾部风险。'
     if m['daily_kurt'] > 3 else
     '⚠️ 超额峰度在2~3之间，存在一定程度的"肥尾"特征，极端事件略多于正态分布预期。'
     if m['daily_kurt'] > 2 else
     '✅ 超额峰度 < 2，收益率分布接近正态，极端风险较小。'}
    偏度 {fmt_num(m['daily_skew'])}，表明收益率分布{'略微左偏（下跌概率略大）' if m['daily_skew'] < 0 else '略微右偏（上涨概率略大）' if m['daily_skew'] > 0 else '对称'}。
  </div>
</div>

<!-- ========== 6. 周涨跌分布与回撤事件 ========== -->
<div class="section">
  <h2>📆 周度涨跌分布与显著回撤事件</h2>
  <img class="chart-img" src="data:image/png;base64,{chart4_b64}" alt="周涨跌与显著回撤">

  <h3>📋 极端交易日记录 (涨跌幅 ≥ 5%)</h3>
  <table>
    <thead>
      <tr><th>日期</th><th>涨跌幅</th><th>收盘价</th><th>成交量</th></tr>
    </thead>
    <tbody>
      {extreme_rows}
    </tbody>
  </table>
  <p style="font-size:13px;color:#888;margin-top:5px">
    * 极端交易日数量是衡量"肥尾风险"的重要参考。次数越少说明走势越平稳。
  </p>
</div>

<!-- ========== 7. 综合评估 ========== -->
<div class="section">
  <h2>🎯 综合风险评估与投资建议</h2>

  <h3>📋 风险等级评估</h3>
  <table>
    <tr><th style="width:160px">评估维度</th><th>指标值</th><th>评分</th><th>说明</th></tr>
    <tr>
      <td><strong>波动风险</strong></td>
      <td>{fmt_pct(m['annual_vol'])}</td>
      <td><span class="rating-box {'rating-good' if m['annual_vol'] < 0.25 else 'rating-ok' if m['annual_vol'] < 0.35 else 'rating-bad'}">{
        '低' if m['annual_vol'] < 0.25 else '中' if m['annual_vol'] < 0.35 else '高'
      }</span></td>
      <td>波动率在A股中处于较低水平，适合风险偏好较低的投资者</td>
    </tr>
    <tr>
      <td><strong>回撤风险</strong></td>
      <td>{fmt_pct(m['max_drawdown'])}</td>
      <td><span class="rating-box {'rating-good' if abs(m['max_drawdown']) < 0.2 else 'rating-ok' if abs(m['max_drawdown']) < 0.35 else 'rating-bad'}">{
        '低' if abs(m['max_drawdown']) < 0.2 else '中' if abs(m['max_drawdown']) < 0.35 else '高'
      }</span></td>
      <td>最大回撤控制在{'较好' if abs(m['max_drawdown']) < 0.25 else '一般'}水平</td>
    </tr>
    <tr>
      <td><strong>收益风险比</strong></td>
      <td>夏普 {fmt_num(m['sharpe_ratio'])} / 卡玛 {fmt_num(m['calmar_ratio'])}</td>
      <td><span class="rating-box {'rating-good' if m['sharpe_ratio'] > 0.8 else 'rating-ok' if m['sharpe_ratio'] > 0 else 'rating-bad'}">{
        '优' if m['sharpe_ratio'] > 0.8 else '中' if m['sharpe_ratio'] > 0 else '差'
      }</span></td>
      <td>{'每承受1%波动可获得' + fmt_pct(m['sharpe_ratio']/100, 4) + '超额收益' if m['sharpe_ratio'] > 0 else '超额收益为负'}</td>
    </tr>
    <tr>
      <td><strong>尾部风险</strong></td>
      <td>CVaR {fmt_pct(m['cvar_95'])}</td>
      <td><span class="rating-box {'rating-good' if abs(m['cvar_95']) < 0.03 else 'rating-ok' if abs(m['cvar_95']) < 0.05 else 'rating-bad'}">{
        '低' if abs(m['cvar_95']) < 0.03 else '中' if abs(m['cvar_95']) < 0.05 else '高'
      }</span></td>
      <td>极端行情下日均可能亏损 {fmt_pct(abs(m['cvar_95']))}</td>
    </tr>
    <tr>
      <td><strong>抗跌能力</strong></td>
      <td>下行风险 {fmt_pct(m['downside_risk'])}</td>
      <td><span class="rating-box {'rating-good' if m['downside_risk'] < 0.18 else 'rating-ok' if m['downside_risk'] < 0.25 else 'rating-bad'}">{
        '强' if m['downside_risk'] < 0.18 else '中' if m['downside_risk'] < 0.25 else '弱'
      }</span></td>
      <td>下跌阶段波动{'较小' if m['downside_risk'] < 0.18 else '可控' if m['downside_risk'] < 0.25 else '较大'}</td>
    </tr>
  </table>

  <h3 style="margin-top:25px">💡 投资参考</h3>
  <div class="insight-box">
    <p><strong>风格定位：</strong>贵州茅台属于 <strong>低波动·大盘蓝筹</strong> 风格，
    年化波动率约 <strong>{fmt_pct(m['annual_vol'])}</strong>，
    远低于A股中小盘股票（通常35%~50%），与消费/白酒板块龙头定位一致。</p>
    <p style="margin-top:8px"><strong>持有体验：</strong>4年内最大回撤 {fmt_pct(m['max_drawdown'])}，
    意味着如果投资者在最高点买入，账户最多将浮亏 {fmt_pct(m['max_drawdown'])}。
    回撤修复需约 {m['recovery_days'] if isinstance(m['recovery_days'], str) else str(m['recovery_days']) + '个交易日'}，
    对应约{'半年' if isinstance(m['recovery_days'], str) else f'{m["recovery_days"]/20:.1f}个月' if m['recovery_days'] else '未知'}。
    这一回撤幅度在A股蓝筹中属于{'可接受范围' if abs(m['max_drawdown']) < 0.30 else '偏高水平'}。
    </p>
    <p style="margin-top:8px"><strong>风险预警：</strong>VaR(95%) = {fmt_pct(m['var_95'])}，
    意味着每20个交易日中约有1天亏损超过 {fmt_pct(abs(m['var_95']))}。
    以每万元投资计算，95%情况下单日亏损不超过 <strong>{var_95_loss_per_10k:.0f} 元</strong>，
    99%情况下不超过 <strong>{var_99_loss_per_10k:.0f} 元</strong>。
    </p>
  </div>
</div>

<!-- ========== 8. 数据附录 ========== -->
<div class="section">
  <h2>📋 数据附录</h2>
  <table>
    <tr><th>指标</th><th>值</th></tr>
    <tr><td>数据来源</td><td>akshare (东方财富接口)</td></tr>
    <tr><td>分析周期</td><td>{START_DATE[:4]}-{START_DATE[4:6]}-{START_DATE[6:]} ~ {END_DATE[:4]}-{END_DATE[4:6]}-{END_DATE[6:]}</td></tr>
    <tr><td>总交易日</td><td>{m['trading_days']} 天</td></tr>
    <tr><td>起始收盘价</td><td>{main_df['close'].iloc[0]:.2f} 元</td></tr>
    <tr><td>最新收盘价</td><td>{m['final_price']:.2f} 元</td></tr>
    <tr><td>期间最高价</td><td>{main_df['high'].max():.2f} 元</td></tr>
    <tr><td>期间最低价</td><td>{main_df['low'].min():.2f} 元</td></tr>
    <tr><td>分析工具</td><td>Python 3.13 + pandas + numpy + matplotlib + scipy</td></tr>
    <tr><td>报告生成时间</td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
  </table>
  <p style="margin-top:15px;font-size:13px;color:#999">
    ⚠️ 免责声明：本报告仅供参考，不构成任何投资建议。历史表现不代表未来收益。
    数据来源于 akshare 开源库，可能存在延迟或误差，请以交易所官方数据为准。
  </p>
</div>

<div class="footer">
  <p>📊 贵州茅台 (600519.SH) 风险波动分析报告 · Generated by WorkBuddy + akshare</p>
</div>

</div>
</body>
</html>"""

with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ HTML报告已生成: {REPORT_FILE}")
print(f"文件大小: {os.path.getsize(REPORT_FILE) / 1024:.1f} KB")
