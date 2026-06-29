"""
获取腾讯控股(00700.HK)过去两年的日线交易数据
数据源: akshare (免费开源)
"""
import akshare as ak
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# ============ 配置 ============
SYMBOL = "00700"
HK_NAME = "腾讯控股"
START_DATE = "20240629"  # 2年前
END_DATE = "20260629"    # 当前日期

OUTPUT_DIR = r"C:\Users\csd\Documents\task1"
CSV_FILE = os.path.join(OUTPUT_DIR, "00700_HK_tencent_daily_data.csv")
CHART_FILE = os.path.join(OUTPUT_DIR, "00700_HK_tencent_close_price_chart.png")

# ============ 1. 获取港股日线数据 ============
print(f"正在从 akshare 获取 {HK_NAME}({SYMBOL}.HK) 港股日线数据...")

try:
    # 港股历史日线数据
    df = ak.stock_hk_hist(
        symbol=SYMBOL,
        period="daily",
        start_date=START_DATE,
        end_date=END_DATE,
        adjust="qfq"  # 前复权
    )
    print(f"成功获取 {len(df)} 条交易日数据")
except Exception as e:
    print(f"stock_hk_hist 失败: {e}")
    print("尝试使用备用接口 stock_hk_daily...")
    try:
        df = ak.stock_hk_daily(symbol=SYMBOL, adjust="qfq")
        # 过滤日期范围
        df = df[(df['date'] >= START_DATE[:4] + '-' + START_DATE[4:6] + '-' + START_DATE[6:]) &
                (df['date'] <= END_DATE[:4] + '-' + END_DATE[4:6] + '-' + END_DATE[6:])]
        print(f"成功获取 {len(df)} 条交易日数据")
    except Exception as e2:
        print(f"备用接口也失败: {e2}")
        exit(1)

print(f"\n数据列: {list(df.columns)}")
print(f"数据前5行:\n{df.head()}")

# ============ 2. 数据处理 ============
# 重命名列为英文，方便后续使用
column_map = {
    '日期': 'trade_date',
    '开盘': 'open',
    '最高': 'high',
    '最低': 'low',
    '收盘': 'close',
    '涨跌幅': 'pct_chg',
    '涨跌额': 'change',
    '成交量': 'vol',
    '成交额': 'amount',
    'date': 'trade_date',
    'open': 'open',
    'high': 'high',
    'low': 'low',
    'close': 'close',
    'volume': 'vol',
    'amount': 'amount',
}
df.rename(columns={col: column_map.get(col, col) for col in df.columns}, inplace=True)

# 确保日期列是datetime格式
if 'trade_date' in df.columns:
    df['trade_date'] = pd.to_datetime(df['trade_date'])
else:
    # 查找可能的日期列
    for col in df.columns:
        if 'date' in col.lower() or '时间' in col:
            df.rename(columns={col: 'trade_date'}, inplace=True)
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            break

# 按日期排序
df = df.sort_values('trade_date').reset_index(drop=True)

# 转换数值列
numeric_cols = []
for col in ['open', 'high', 'low', 'close', 'vol', 'amount', 'pct_chg', 'change']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        numeric_cols.append(col)

print(f"\n📊 数据概览:")
print(f"  日期范围: {df['trade_date'].min().date()} ~ {df['trade_date'].max().date()}")
print(f"  总交易天数: {len(df)}")
print(f"  最新收盘价: {df['close'].iloc[-1]:.2f}" if 'close' in df.columns else "")
print(f"  最高价: {df['close' if 'close' in df.columns else 'high'].max():.2f}")
print(f"  最低价: {df['close' if 'close' in df.columns else 'low'].min():.2f}")

# ============ 3. 保存CSV ============
df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
print(f"\n✅ 数据已保存至: {CSV_FILE}")

# ============ 4. 画收盘价曲线图 ============
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(14, 7))

close_col = 'close' if 'close' in df.columns else '收盘'
trade_date_col = 'trade_date'

# 绘制收盘价曲线
ax.plot(df[trade_date_col], df[close_col], color='#0055A4', linewidth=1.8, label='收盘价')
ax.fill_between(df[trade_date_col], df[close_col], alpha=0.1, color='#0055A4')

# 美化
ax.set_title(f'腾讯控股 (00700.HK) 过去两年每日收盘价走势', fontsize=16, fontweight='bold', pad=15)
ax.set_xlabel('交易日期', fontsize=12)
ax.set_ylabel('收盘价 (港元)', fontsize=12)

# 日期格式
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
plt.xticks(rotation=45)

ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(fontsize=11)

# 标注最新价格
latest_date = df[trade_date_col].iloc[-1]
latest_close = df[close_col].iloc[-1]
ax.annotate(f'{latest_close:.2f}',
            xy=(latest_date, latest_close),
            xytext=(15, 10), textcoords='offset points',
            fontsize=11, fontweight='bold', color='#0055A4',
            arrowprops=dict(arrowstyle='->', color='#0055A4', lw=1.5))

# 标注最高和最低点
max_idx = df[close_col].idxmax()
min_idx = df[close_col].idxmin()
ax.annotate(f'最高: {df[close_col].iloc[max_idx]:.2f}',
            xy=(df[trade_date_col].iloc[max_idx], df[close_col].iloc[max_idx]),
            xytext=(10, -20), textcoords='offset points',
            fontsize=10, color='green', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='green', lw=1))
ax.annotate(f'最低: {df[close_col].iloc[min_idx]:.2f}',
            xy=(df[trade_date_col].iloc[min_idx], df[close_col].iloc[min_idx]),
            xytext=(10, 15), textcoords='offset points',
            fontsize=10, color='red', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='red', lw=1))

plt.tight_layout()
plt.savefig(CHART_FILE, dpi=150, bbox_inches='tight')
print(f"✅ 收盘价曲线图已保存至: {CHART_FILE}")
plt.close()

print(f"\n{'='*50}")
print(f"🎉 任务完成！")
print(f"{'='*50}")
print(f"📊 CSV数据: {CSV_FILE}")
print(f"📈 收盘价图: {CHART_FILE}")
