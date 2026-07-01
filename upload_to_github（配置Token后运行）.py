# -*- coding: utf-8 -*-
"""
GitHub 仓库文件上传脚本
使用方法：
1. 在 GitHub 上创建一个有 repo 权限的 Personal Access Token
2. 修改下面的 GITHUB_TOKEN 为你的 Token
3. 运行本脚本
"""

import requests
import base64
import os
import json
from datetime import datetime

# ============== 配置区域 ==============
GITHUB_TOKEN = "在这里输入你的GitHub Token"
REPO_OWNER = "hupige"
REPO_NAME = "ai_quant"
BRANCH = "main"
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
# ======================================

GITHUB_API = "https://api.github.com"
headers = {
    "Authorization": "token {}".format(GITHUB_TOKEN),
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
}

FILES_TO_UPLOAD = [
    "README.md",
    "stock_analysis.py",
    "generate_html_report.py",
    "data/600519_贵州茅台_日线数据.csv",
    "report/600519_贵州茅台_风险分析报告.txt",
    "report/600519_贵州茅台_风险分析报告.html",
    "report/600519_贵州茅台_风险分析图表.png",
]


def get_file_sha(path):
    url = "{}/repos/{}/{}/contents/{}?ref={}".format(
        GITHUB_API, REPO_OWNER, REPO_NAME, path, BRANCH
    )
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, dict) and "sha" in data:
            return data["sha"]
    return None


def upload_file(local_path, remote_path):
    full_local_path = os.path.join(LOCAL_DIR, local_path.replace('/', os.sep))
    
    if not os.path.exists(full_local_path):
        print("  跳过不存在的文件: {}".format(local_path))
        return False
    
    file_size = os.path.getsize(full_local_path)
    print("  上传: {} ({:.2f} KB)".format(remote_path, file_size / 1024), end=" ")
    
    with open(full_local_path, 'rb') as f:
        content = f.read()
    
    content_b64 = base64.b64encode(content).decode('utf-8')
    sha = get_file_sha(remote_path)
    
    url = "{}/repos/{}/{}/contents/{}".format(
        GITHUB_API, REPO_OWNER, REPO_NAME, remote_path
    )
    
    data = {
        "message": "添加股票风险分析文件 - {}".format(datetime.now().strftime('%Y-%m-%d')),
        "content": content_b64,
        "branch": BRANCH
    }
    
    if sha:
        data["sha"] = sha
    
    try:
        r = requests.put(url, headers=headers, data=json.dumps(data), timeout=120)
        if r.status_code in (200, 201):
            print("成功")
            return True
        else:
            print("失败")
            print("    错误: {} - {}".format(r.status_code, r.text[:200]))
            return False
    except Exception as e:
        print("异常: {}".format(str(e)))
        return False


def create_readme():
    readme_content = """# AI Quant - A股股票风险分析

基于 AkShare 数据源的A股股票数据下载与风险分析系统。

## 项目功能

1. **数据下载**: 从东方财富网获取A股日交易数据（前复权）
2. **数据存储**: CSV格式保存，便于后续分析
3. **风险分析**: 专业的风险指标计算与分析报告
4. **可视化**: 精美的HTML格式分析报告，图文并茂

## 文件说明

| 文件 | 说明 |
|------|------|
| `stock_analysis.py` | 主脚本：数据下载 + 风险分析 + 文字/图表报告 |
| `generate_html_report.py` | 精美HTML报告生成脚本 |
| `data/` | 股票数据目录（CSV格式） |
| `report/` | 分析报告目录（txt/html/png） |

## 分析指标

- **收益指标**: 累计收益率、年化收益率
- **风险指标**: 年化波动率、下行波动率、最大回撤
- **风险调整收益**: 夏普比率、索提诺比率、Beta、Alpha
- **在险价值**: VaR(95%)、VaR(99%)、CVaR(95%)
- **交易统计**: 胜率、盈亏比、涨跌天数

## 使用方法

```bash
# 下载数据并生成所有报告
python stock_analysis.py

# 仅生成精美HTML报告（需已有CSV数据）
python generate_html_report.py
```

## 分析标的

- **股票**: 贵州茅台 (600519)
- **数据区间**: 约4年日交易数据
- **数据来源**: 东方财富网（AkShare接口）

## 免责声明

本项目仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。

---
*由 AI 自动生成*
"""
    
    readme_local = os.path.join(LOCAL_DIR, "README.md")
    with open(readme_local, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("README.md 已创建")


def main():
    print("=" * 60)
    print("  GitHub 仓库文件上传")
    print("=" * 60)
    print("仓库: {}/{}".format(REPO_OWNER, REPO_NAME))
    print("分支: {}".format(BRANCH))
    print()
    
    if GITHUB_TOKEN == "在这里输入你的GitHub Token" or not GITHUB_TOKEN:
        print("错误：请先在脚本顶部设置 GITHUB_TOKEN")
        print()
        print("如何获取Token：")
        print("  1. 访问 https://github.com/settings/tokens?type=beta")
        print("  2. 点击 'Generate new token'")
        print("  3. 填写名称，选择过期时间")
        print("  4. 在 'Repository access' 中选择 'Only select repositories'")
        print("     然后选择 ai_quant 仓库")
        print("  5. 在 'Permissions' -> 'Repository permissions' 中")
        print("     找到 'Contents'，设置为 'Read and write'")
        print("  6. 点击底部 'Generate token'")
        print("  7. 复制生成的Token，填入脚本顶部")
        print()
        return
    
    print("检查仓库连接...")
    url = "{}/repos/{}/{}".format(GITHUB_API, REPO_OWNER, REPO_NAME)
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        print("无法连接到仓库: {} - {}".format(r.status_code, r.text[:200]))
        return
    print("仓库连接成功")
    print()
    
    create_readme()
    print()
    
    success_count = 0
    fail_count = 0
    
    print("开始上传文件...")
    print()
    
    for f in FILES_TO_UPLOAD:
        if upload_file(f, f):
            success_count += 1
        else:
            fail_count += 1
        print()
    
    print("=" * 60)
    print("上传完成！")
    print("=" * 60)
    print("  成功: {} 个文件".format(success_count))
    print("  失败: {} 个文件".format(fail_count))
    print()
    print("仓库地址: https://github.com/{}/{}".format(REPO_OWNER, REPO_NAME))
    print("=" * 60)


if __name__ == '__main__':
    main()
