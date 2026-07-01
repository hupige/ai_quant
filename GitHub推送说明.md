# 推送到 GitHub 说明

当前环境没有安装 Git 客户端，且您提供的 GitHub Token 没有仓库写入权限。
这里提供两种推送方式，请选择适合您的方式。

---

## 方式一：使用 Git 命令行（推荐）

### 前置条件
- 电脑上已安装 Git（https://git-scm.com/download/win）
- 能正常访问 GitHub

### 操作步骤

1. **将整个 `d:\task1` 文件夹复制到有 Git 的电脑上**

2. **双击运行 `推送到GitHub.bat`**
   
   或者手动执行以下命令：
   ```bash
   cd d:\task1
   git init
   git remote add origin https://github.com/hupige/ai_quant.git
   git add -A
   git commit -m "添加A股股票风险分析代码和报告"
   git push -u origin main
   ```

3. **按照提示输入 GitHub 用户名和密码（或Token）**

> 注意：如果远程分支是 `master` 而不是 `main`，请将最后一行改为：
> `git push -u origin master`

---

## 方式二：使用 Python 脚本 + GitHub Token

### 前置条件
- 电脑上已安装 Python
- 有一个具有仓库写入权限的 GitHub Personal Access Token

### 创建具有写入权限的 Token 步骤

1. 访问：https://github.com/settings/tokens?type=beta
2. 点击 **"Generate new token"**
3. 填写 Token 名称（如：ai_quant_upload）
4. 选择过期时间
5. **Repository access** 选择 **"Only select repositories"**
   - 在下拉框中选择 `ai_quant` 仓库
6. **Permissions** 部分，找到 **Repository permissions**
   - 找到 **Contents**，设置为 **"Read and write"**
7. 拉到页面底部，点击 **"Generate token"**
8. **复制生成的 Token**（只显示一次，务必保存好）

### 使用脚本

1. 打开文件 `upload_to_github（配置Token后运行）.py`
2. 修改第 14 行的 `GITHUB_TOKEN` 为你刚生成的 Token
3. 运行脚本：
   ```bash
   python "upload_to_github（配置Token后运行）.py"
   ```

---

## 需要推送的文件清单

| 文件/目录 | 大小 | 说明 |
|----------|------|------|
| `README.md` | ~2KB | 项目说明文档 |
| `stock_analysis.py` | ~18KB | 主分析脚本（下载+分析+报告） |
| `generate_html_report.py` | ~20KB | HTML报告生成脚本 |
| `推送到GitHub.bat` | ~2KB | 一键Git推送脚本（Windows） |
| `data/600519_贵州茅台_日线数据.csv` | ~100KB | 4年日交易数据 |
| `report/600519_贵州茅台_风险分析报告.txt` | ~3KB | 文字版风险分析报告 |
| `report/600519_贵州茅台_风险分析报告.html` | ~656KB | 精美HTML版报告（内嵌图表） |
| `report/600519_贵州茅台_风险分析图表.png` | ~500KB | 6合1分析图表 |

---

## 常见问题

### Q: 推送时报错 `fatal: Authentication failed`
A: 密码处请使用 GitHub Personal Access Token，而不是账号密码。

### Q: 推送时报错 `src refspec main does not match any`
A: 可能分支名是 master，试试 `git push -u origin master`

### Q: HTML文件太大，GitHub显示有问题？
A: HTML文件中的图表是base64内嵌的，文件较大是正常的。GitHub可以正常存储和下载。
在 GitHub 页面上点击 HTML 文件后，再点击 "Download" 或 "Raw" 查看。

### Q: 如何在 GitHub Pages 上预览 HTML 报告？
A: 
1. 进入仓库 Settings -> Pages
2. Source 选择 "Deploy from a branch"
3. Branch 选择 main / (root)
4. 保存后等待几分钟，访问 `https://hupige.github.io/ai_quant/report/600519_贵州茅台_风险分析报告.html`
