# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import numpy as np
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

STOCK_CODE = '600519'
STOCK_NAME = '贵州茅台'
DATA_DIR = r'd:\task1\data'
REPORT_DIR = r'd:\task1\report'


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)


def get_market_id(stock_code):
    if stock_code.startswith('6'):
        return '1'
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        return '0'
    elif stock_code.startswith('8') or stock_code.startswith('4'):
        return '0'
    else:
        return '1'


def download_stock_data_direct(stock_code, start_date_str, end_date_str, adjust='qfq'):
    market_id = get_market_id(stock_code)
    secid = '{}.{}'.format(market_id, stock_code)
    
    adjust_dict = {'qfq': '1', 'hfq': '2', '': '0'}
    
    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": "101",
        "fqt": adjust_dict.get(adjust, '1'),
        "secid": secid,
        "beg": start_date_str,
        "end": end_date_str,
        "_": "1623766962675",
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data_json = r.json()
    
    if not (data_json.get("data") and data_json["data"].get("klines")):
        return pd.DataFrame()
    
    klines = data_json["data"]["klines"]
    temp_df = pd.DataFrame([item.split(",") for item in klines])
    temp_df.columns = [
        "日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额",
        "振幅", "涨跌幅", "涨跌额", "换手率",
    ]
    
    numeric_cols = ["开盘", "收盘", "最高", "最低", "成交量", "成交额",
                    "振幅", "涨跌幅", "涨跌额", "换手率"]
    for col in numeric_cols:
        temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
    
    return temp_df


def download_index_data_direct(index_code, start_date_str, end_date_str):
    secid = '1.{}'.format(index_code)
    
    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": "101",
        "fqt": "0",
        "secid": secid,
        "beg": start_date_str,
        "end": end_date_str,
        "_": "1623766962675",
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data_json = r.json()
        
        if not (data_json.get("data") and data_json["data"].get("klines")):
            return pd.DataFrame()
        
        klines = data_json["data"]["klines"]
        temp_df = pd.DataFrame([item.split(",") for item in klines])
        temp_df.columns = ["date", "open", "close", "high", "low", "volume", "amount", "amplitude", "pct_chg", "change", "turnover"]
        
        numeric_cols = ["open", "close", "high", "low", "volume", "amount"]
        for col in numeric_cols:
            if col in temp_df.columns:
                temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        
        temp_df['date'] = pd.to_datetime(temp_df['date'])
        return temp_df
    except Exception as e:
        print("直接获取指数数据失败: {}".format(str(e)[:100]))
        return pd.DataFrame()


def download_stock_data():
    print("=" * 60)
    print("正在下载 {} ({}) 的日交易数据...".format(STOCK_NAME, STOCK_CODE))
    print("=" * 60)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=4 * 365)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    print("数据区间: {} 至 {}".format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

    df = None
    try:
        print("尝试通过akshare接口下载...")
        df = ak.stock_zh_a_hist(
            symbol=STOCK_CODE,
            period="daily",
            start_date=start_date_str,
            end_date=end_date_str,
            adjust="qfq"
        )
        if df is not None and len(df) > 0:
            print("akshare接口下载成功")
    except Exception as e:
        print("akshare接口下载失败，尝试直接调用东方财富API... 错误: {}".format(str(e)[:100]))

    if df is None or len(df) == 0:
        print("使用直接API调用方式下载...")
        df = download_stock_data_direct(STOCK_CODE, start_date_str, end_date_str, adjust='qfq')

    if df is None or len(df) == 0:
        raise Exception("所有数据下载方式均失败")

    df.columns = [c.strip() for c in df.columns]
    print("下载完成，共 {} 条记录".format(len(df)))
    print("列名: {}".format(list(df.columns)))

    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期').reset_index(drop=True)

    csv_path = os.path.join(DATA_DIR, '{}_{}_日线数据.csv'.format(STOCK_CODE, STOCK_NAME))
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print("数据已保存至: {}".format(csv_path))

    return df, csv_path


def calculate_risk_metrics(df):
    print("\n" + "=" * 60)
    print("正在计算风险分析指标...")
    print("=" * 60)

    close_col = '收盘' if '收盘' in df.columns else '收盘价'
    date_col = '日期' if '日期' in df.columns else 'date'
    high_col = '最高' if '最高' in df.columns else '最高价'
    low_col = '最低' if '最低' in df.columns else '最低价'
    volume_col = '成交量' if '成交量' in df.columns else 'volume'
    turnover_col = '换手率' if '换手率' in df.columns else 'turnover'

    df = df.copy()
    df['收益率'] = df[close_col].pct_change()
    df['对数收益率'] = np.log(df[close_col] / df[close_col].shift(1))
    df['收益率_绝对值'] = df['收益率'].abs()

    metrics = {}

    total_days = len(df)
    start_price = df[close_col].iloc[0]
    end_price = df[close_col].iloc[-1]
    total_return = (end_price - start_price) / start_price
    annualized_return = (1 + total_return) ** (252 / total_days) - 1

    metrics['总交易日数'] = total_days
    metrics['起始价格'] = round(start_price, 2)
    metrics['结束价格'] = round(end_price, 2)
    metrics['区间最高价格'] = round(df[high_col].max(), 2)
    metrics['区间最低价格'] = round(df[low_col].min(), 2)
    metrics['累计收益率'] = '{:.2%}'.format(total_return)
    metrics['年化收益率'] = '{:.2%}'.format(annualized_return)

    daily_vol = df['收益率'].std()
    annualized_vol = daily_vol * np.sqrt(252)
    downside_returns = df['收益率'][df['收益率'] < 0]
    downside_vol = downside_returns.std() * np.sqrt(252)

    metrics['日波动率'] = '{:.4%}'.format(daily_vol)
    metrics['年化波动率'] = '{:.2%}'.format(annualized_vol)
    metrics['下行波动率'] = '{:.2%}'.format(downside_vol)

    risk_free_rate = 0.02
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_vol if annualized_vol > 0 else 0
    sortino_ratio = (annualized_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0

    metrics['夏普比率'] = round(sharpe_ratio, 3)
    metrics['索提诺比率'] = round(sortino_ratio, 3)

    cumulative = (1 + df['收益率'].fillna(0)).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    max_dd_end_idx = drawdown.idxmin()
    max_dd_start_idx = running_max[:max_dd_end_idx].idxmax()

    metrics['最大回撤'] = '{:.2%}'.format(max_drawdown)
    metrics['最大回撤开始日期'] = str(df[date_col].iloc[max_dd_start_idx].date())
    metrics['最大回撤结束日期'] = str(df[date_col].iloc[max_dd_end_idx].date())

    var_95 = np.percentile(df['收益率'].dropna(), 5)
    var_99 = np.percentile(df['收益率'].dropna(), 1)
    cvar_95 = df['收益率'][df['收益率'] <= var_95].mean()

    metrics['VaR(95%)'] = '{:.4%}'.format(var_95)
    metrics['VaR(99%)'] = '{:.4%}'.format(var_99)
    metrics['CVaR(95%)'] = '{:.4%}'.format(cvar_95)

    positive_days = len(df[df['收益率'] > 0])
    negative_days = len(df[df['收益率'] < 0])
    flat_days = len(df[df['收益率'] == 0])
    win_rate = positive_days / (positive_days + negative_days) if (positive_days + negative_days) > 0 else 0

    avg_gain = df['收益率'][df['收益率'] > 0].mean()
    avg_loss = df['收益率'][df['收益率'] < 0].mean()
    profit_loss_ratio = abs(avg_gain / avg_loss) if avg_loss != 0 else 0

    metrics['上涨天数'] = positive_days
    metrics['下跌天数'] = negative_days
    metrics['平盘天数'] = flat_days
    metrics['胜率'] = '{:.2%}'.format(win_rate)
    metrics['平均涨幅'] = '{:.4%}'.format(avg_gain)
    metrics['平均跌幅'] = '{:.4%}'.format(avg_loss)
    metrics['盈亏比'] = round(profit_loss_ratio, 3)

    df['MA5'] = df[close_col].rolling(5).mean()
    df['MA20'] = df[close_col].rolling(20).mean()
    df['MA60'] = df[close_col].rolling(60).mean()
    df['MA250'] = df[close_col].rolling(250).mean()
    df['波动率_20日'] = df['收益率'].rolling(20).std() * np.sqrt(252)
    df['波动率_60日'] = df['收益率'].rolling(60).std() * np.sqrt(252)

    df['回撤'] = drawdown

    beta = None
    alpha = None
    try:
        end_date = df[date_col].iloc[-1]
        start_date = df[date_col].iloc[0]
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        index_df = None
        try:
            index_df = ak.stock_zh_index_daily(symbol="sh000300")
            index_df['date'] = pd.to_datetime(index_df['date'])
            index_df = index_df[(index_df['date'] >= start_date) & (index_df['date'] <= end_date)]
        except Exception as idx_e:
            print("akshare获取指数数据失败，尝试直接API... 错误: {}".format(str(idx_e)[:80]))
            index_df = download_index_data_direct('000300', start_date_str, end_date_str)
        
        if index_df is not None and len(index_df) > 30:
            index_df['指数收益率'] = index_df['close'].pct_change()
            date_col_idx = 'date' if 'date' in index_df.columns else '日期'
            
            merged = pd.merge(
                df[[date_col, '收益率']].dropna(),
                index_df[[date_col_idx, '指数收益率']].dropna(),
                left_on=date_col,
                right_on=date_col_idx,
                how='inner'
            )

            if len(merged) > 30:
                cov_matrix = np.cov(merged['收益率'].dropna(), merged['指数收益率'].dropna())
                beta = cov_matrix[0, 1] / cov_matrix[1, 1]
                alpha = annualized_return - (risk_free_rate + beta * ((merged['指数收益率'].mean() * 252) - risk_free_rate))
                metrics['Beta系数'] = round(beta, 3)
                metrics['Alpha'] = '{:.2%}'.format(alpha)
    except Exception as e:
        print("计算Beta/Alpha时出错: {}".format(str(e)))

    for key, value in metrics.items():
        print("  {}: {}".format(key, value))

    return metrics, df


def generate_report(metrics, df, csv_path):
    print("\n" + "=" * 60)
    print("正在生成风险分析报告...")
    print("=" * 60)

    date_col = '日期' if '日期' in df.columns else 'date'
    close_col = '收盘' if '收盘' in df.columns else '收盘价'

    report_path = os.path.join(REPORT_DIR, '{}_{}_风险分析报告.txt'.format(STOCK_CODE, STOCK_NAME))

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("        {} ({}) 股票风险分析报告\n".format(STOCK_NAME, STOCK_CODE))
        f.write("=" * 70 + "\n\n")
        f.write("报告生成时间: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write("分析区间: {} 至 {}\n".format(
            str(df[date_col].iloc[0].date()),
            str(df[date_col].iloc[-1].date())
        ))
        f.write("数据来源: AkShare (前复权)\n\n")

        f.write("-" * 70 + "\n")
        f.write("一、基本行情概览\n")
        f.write("-" * 70 + "\n")
        basic_keys = ['总交易日数', '起始价格', '结束价格', '区间最高价格',
                      '区间最低价格', '累计收益率', '年化收益率']
        for k in basic_keys:
            if k in metrics:
                f.write("  {:<20s}: {}\n".format(k, metrics[k]))
        f.write("\n")

        f.write("-" * 70 + "\n")
        f.write("二、波动率风险指标\n")
        f.write("-" * 70 + "\n")
        vol_keys = ['日波动率', '年化波动率', '下行波动率']
        for k in vol_keys:
            if k in metrics:
                f.write("  {:<20s}: {}\n".format(k, metrics[k]))
        f.write("\n")
        f.write("  说明: \n")
        f.write("    - 年化波动率衡量整体风险水平，数值越高风险越大\n")
        f.write("    - 下行波动率仅考虑负收益波动，更贴近实际亏损风险\n")
        f.write("    - A股个股年化波动率通常在20%-50%之间\n\n")

        f.write("-" * 70 + "\n")
        f.write("三、风险调整收益指标\n")
        f.write("-" * 70 + "\n")
        perf_keys = ['夏普比率', '索提诺比率']
        if 'Beta系数' in metrics:
            perf_keys.append('Beta系数')
            perf_keys.append('Alpha')
        for k in perf_keys:
            if k in metrics:
                f.write("  {:<20s}: {}\n".format(k, metrics[k]))
        f.write("\n")
        f.write("  说明: \n")
        f.write("    - 夏普比率 > 1: 风险调整后收益优于无风险利率\n")
        f.write("    - 索提诺比率: 侧重下行风险调整，数值越高越好\n")
        f.write("    - Beta系数: >1 表示波动大于大盘，<1 表示波动小于大盘\n")
        f.write("    - Alpha: 超出大盘风险调整收益的超额收益\n\n")

        f.write("-" * 70 + "\n")
        f.write("四、回撤风险指标\n")
        f.write("-" * 70 + "\n")
        dd_keys = ['最大回撤', '最大回撤开始日期', '最大回撤结束日期']
        for k in dd_keys:
            if k in metrics:
                f.write("  {:<20s}: {}\n".format(k, metrics[k]))
        f.write("\n")
        f.write("  说明: 最大回撤反映历史最坏情况下的亏损幅度，是重要的风险指标\n\n")

        f.write("-" * 70 + "\n")
        f.write("五、在险价值 (VaR) 分析\n")
        f.write("-" * 70 + "\n")
        var_keys = ['VaR(95%)', 'VaR(99%)', 'CVaR(95%)']
        for k in var_keys:
            if k in metrics:
                f.write("  {:<20s}: {}\n".format(k, metrics[k]))
        f.write("\n")
        f.write("  说明: \n")
        f.write("    - VaR(95%): 在95%置信水平下，单日最大亏损不超过该值\n")
        f.write("    - VaR(99%): 在99%置信水平下，单日最大亏损不超过该值\n")
        f.write("    - CVaR(95%): 当损失超过VaR时的平均损失，衡量尾部风险\n\n")

        f.write("-" * 70 + "\n")
        f.write("六、涨跌分布统计\n")
        f.write("-" * 70 + "\n")
        dist_keys = ['上涨天数', '下跌天数', '平盘天数', '胜率',
                     '平均涨幅', '平均跌幅', '盈亏比']
        for k in dist_keys:
            if k in metrics:
                f.write("  {:<20s}: {}\n".format(k, metrics[k]))
        f.write("\n")
        f.write("  说明: 盈亏比 > 1 且胜率 > 50% 表示整体交易质量较好\n\n")

        f.write("-" * 70 + "\n")
        f.write("七、综合风险评估\n")
        f.write("-" * 70 + "\n")

        risk_level = "中等"
        risk_comment = ""
        annual_vol_val = float(metrics['年化波动率'].strip('%')) / 100
        max_dd_val = float(metrics['最大回撤'].strip('%')) / 100

        if annual_vol_val < 0.25 and abs(max_dd_val) < 0.3:
            risk_level = "较低"
            risk_comment = "该股票波动率和回撤均处于较低水平，风险相对可控。"
        elif annual_vol_val > 0.45 or abs(max_dd_val) > 0.5:
            risk_level = "较高"
            risk_comment = "该股票波动率和/或回撤较大，风险水平较高，需谨慎投资。"
        else:
            risk_level = "中等"
            risk_comment = "该股票风险水平处于A股个股中等区间，需结合自身风险承受能力决策。"

        f.write("  整体风险等级: {}\n".format(risk_level))
        f.write("  风险评估: {}\n\n".format(risk_comment))

        f.write("  投资建议: \n")
        sharpe_val = metrics['夏普比率']
        if sharpe_val > 1.5:
            f.write("    - 风险调整后收益优秀，可考虑配置\n")
        elif sharpe_val > 1.0:
            f.write("    - 风险调整后收益良好，可适度关注\n")
        elif sharpe_val > 0.5:
            f.write("    - 风险调整后收益一般，需谨慎评估\n")
        else:
            f.write("    - 风险调整后收益偏低，建议观望或寻找替代品\n")

        if 'Beta系数' in metrics:
            beta_val = metrics['Beta系数']
            if beta_val > 1.2:
                f.write("    - Beta较高，进攻性强，适合牛市配置\n")
            elif beta_val < 0.8:
                f.write("    - Beta较低，防御性强，适合熊市配置\n")
            else:
                f.write("    - Beta接近1，与大盘同步性较高\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write("                      报告结束\n")
        f.write("=" * 70 + "\n")
        f.write("\n免责声明: 本报告基于历史数据计算，不构成投资建议。\n")
        f.write("         投资有风险，入市需谨慎。\n")

    print("文字报告已保存至: {}".format(report_path))

    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle('{} ({}) 风险分析图表'.format(STOCK_NAME, STOCK_CODE), fontsize=14, fontweight='bold')

    dates = df[date_col]
    ax1 = axes[0, 0]
    ax1.plot(dates, df[close_col], label='收盘价', color='blue', linewidth=0.8)
    if 'MA20' in df.columns:
        ax1.plot(dates, df['MA20'], label='MA20', color='orange', linewidth=0.8, alpha=0.8)
    if 'MA60' in df.columns:
        ax1.plot(dates, df['MA60'], label='MA60', color='green', linewidth=0.8, alpha=0.8)
    ax1.set_title('股价走势')
    ax1.set_ylabel('价格 (元)')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    ax2 = axes[0, 1]
    cumulative = (1 + df['收益率'].fillna(0)).cumprod()
    ax2.plot(dates, cumulative, label='累计净值', color='purple', linewidth=0.8)
    ax2.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    ax2.set_title('累计收益率曲线')
    ax2.set_ylabel('累计净值')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    ax3 = axes[1, 0]
    if '波动率_20日' in df.columns:
        ax3.plot(dates, df['波动率_20日'] * 100, label='20日年化波动率', color='red', linewidth=0.8)
    if '波动率_60日' in df.columns:
        ax3.plot(dates, df['波动率_60日'] * 100, label='60日年化波动率', color='darkred', linewidth=0.8)
    ax3.set_title('滚动波动率')
    ax3.set_ylabel('年化波动率 (%)')
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    ax4 = axes[1, 1]
    if '回撤' in df.columns:
        ax4.fill_between(dates, df['回撤'] * 100, 0, color='red', alpha=0.4)
        ax4.plot(dates, df['回撤'] * 100, color='darkred', linewidth=0.6)
    ax4.set_title('回撤曲线')
    ax4.set_ylabel('回撤 (%)')
    ax4.grid(True, alpha=0.3)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    ax5 = axes[2, 0]
    returns = df['收益率'].dropna() * 100
    ax5.hist(returns, bins=60, color='steelblue', edgecolor='white', alpha=0.8, density=True)
    ax5.axvline(x=returns.mean(), color='red', linestyle='--', linewidth=1, label='均值')
    ax5.axvline(x=np.percentile(returns, 5), color='orange', linestyle='--', linewidth=1, label='VaR 95%')
    ax5.set_title('日收益率分布')
    ax5.set_xlabel('日收益率 (%)')
    ax5.set_ylabel('频率密度')
    ax5.legend(loc='best')
    ax5.grid(True, alpha=0.3)

    ax6 = axes[2, 1]
    yearly_returns = {}
    df_year = df.copy()
    df_year['year'] = df_year[date_col].dt.year
    for year, group in df_year.groupby('year'):
        if len(group) > 20:
            y_return = (group[close_col].iloc[-1] / group[close_col].iloc[0] - 1) * 100
            yearly_returns[year] = y_return
    if yearly_returns:
        years = list(yearly_returns.keys())
        values = list(yearly_returns.values())
        colors = ['green' if v >= 0 else 'red' for v in values]
        ax6.bar([str(y) for y in years], values, color=colors, alpha=0.7)
        ax6.axhline(y=0, color='black', linewidth=0.5)
    ax6.set_title('年度收益率')
    ax6.set_ylabel('收益率 (%)')
    ax6.grid(True, alpha=0.3, axis='y')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    chart_path = os.path.join(REPORT_DIR, '{}_{}_风险分析图表.png'.format(STOCK_CODE, STOCK_NAME))
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    print("图表已保存至: {}".format(chart_path))

    return report_path, chart_path


def main():
    print("\n" + "=" * 60)
    print("   A股股票数据下载与风险分析系统")
    print("=" * 60 + "\n")

    ensure_dirs()

    df, csv_path = download_stock_data()

    if df is None or len(df) < 100:
        print("数据量不足，无法进行有效风险分析")
        return

    metrics, df_with_indicators = calculate_risk_metrics(df)

    report_path, chart_path = generate_report(metrics, df_with_indicators, csv_path)

    print("\n" + "=" * 60)
    print("任务完成！")
    print("=" * 60)
    print("  数据文件: {}".format(csv_path))
    print("  分析报告: {}".format(report_path))
    print("  分析图表: {}".format(chart_path))
    print("=" * 60)


if __name__ == '__main__':
    main()
