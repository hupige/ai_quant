"""
获取贵州茅台(600519.SH)过去一年的日线交易数据
数据源: Tushare Pro
"""
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import json
import os

# ============ 配置 ============
TOKEN = "8b4070e8ec0cd50454f749f82243b8fb879a2c01cc8d354db1c91ca1"
TS_CODE = "600519.SH"
API_URL = "https://api.tushare.pro"

# 当前日期是2026年6月29日，过去一年
END_DATE = "20260629"
START_DATE = "20250629"  # 一年前

OUTPUT_DIR = r"C:\Users\csd\Documents\task1"
CSV_FILE = os.path.join(OUTPUT_DIR, "600519_SH_daily_data.csv")
CHART_FILE = os.path.join(OUTPUT_DIR, "600519_SH_close_price_chart.png")

# ============ 1. 获取数据 ============
print("正在从Tushare Pro获取贵州茅台(600519.SH)数据...")

payload = {
    "api_name": "daily",
    "token": TOKEN,
    "params": {
        "ts_code": TS_CODE,
        "start_date": START_DATE,
        "end_date": END_DATE
    },
    "fields": "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"
}

response = requests.post(API_URL, json=payload)
data = response.json()

if data.get("code") != 0:
    print(f"API请求失败: {data.get('msg', '未知错误')}")
    print(f"完整响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    exit(1)

records = data.get("data", {}).get("items", [])
fields = data.get("data", {}).get("fields", [])

if not records:
    print("未获取到数据记录")
    exit(1)

print(f"成功获取 {len(records)} 条交易日数据")

# ============ 2. 转为DataFrame ============
df = pd.DataFrame(records, columns=fields)

# 数据类型转换
df['trade_date'] = pd.to_datetime(df['trade_date'])
df = df.sort_values('trade_date')  # 按日期升序排列

numeric_cols = ['open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"\n数据概览:")
print(f"  日期范围: {df['trade_date'].min().date()} ~ {df['trade_date'].max().date()}")
print(f"  总交易天数: {len(df)}")
print(f"  最新收盘价: {df['close'].iloc[-1]:.2f}")
print(f"  最高价: {df['high'].max():.2f}")
print(f"  最低价: {df['low'].min():.2f}")
print(f"  平均收盘价: {df['close'].mean():.2f}")

# ============ 3. 保存CSV ============
df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
print(f"\n✅ 数据已保存至: {CSV_FILE}")

# ============ 4. 画收盘价曲线图 ============
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(14, 7))

# 绘制收盘价曲线
ax.plot(df['trade_date'], df['close'], color='#E60012', linewidth=1.8, label='收盘价')
ax.fill_between(df['trade_date'], df['close'], alpha=0.1, color='#E60012')

# 美化
ax.set_title('贵州茅台 (600519.SH) 过去一年每日收盘价走势', fontsize=16, fontweight='bold', pad=15)
ax.set_xlabel('交易日期', fontsize=12)
ax.set_ylabel('收盘价 (元)', fontsize=12)

# 日期格式
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator())
plt.xticks(rotation=45)

ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(fontsize=11)

# 标注最新价格
latest_date = df['trade_date'].iloc[-1]
latest_close = df['close'].iloc[-1]
ax.annotate(f'{latest_close:.2f}', 
            xy=(latest_date, latest_close),
            xytext=(10, 10), textcoords='offset points',
            fontsize=11, fontweight='bold', color='#E60012',
            arrowprops=dict(arrowstyle='->', color='#E60012', lw=1.5))

plt.tight_layout()
plt.savefig(CHART_FILE, dpi=150, bbox_inches='tight')
print(f"✅ 收盘价曲线图已保存至: {CHART_FILE}")
plt.close()

print("\n===== 任务完成 =====")
print(f"📊 数据文件: {CSV_FILE}")
print(f"📈 图表文件: {CHART_FILE}")
