@echo off
chcp 65001 >nul
echo ============================================================
echo    A股股票风险分析项目 - GitHub一键推送脚本
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/5] 检查Git是否安装...
git --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo 错误：未检测到Git！
    echo 请先安装Git：https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)
echo Git已安装
echo.

echo [2/5] 初始化Git仓库...
if not exist ".git" (
    git init
    echo 新仓库已初始化
) else (
    echo 仓库已存在
)
echo.

echo [3/5] 添加远程仓库...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/hupige/ai_quant.git
echo 远程仓库已设置
echo.

echo [4/5] 添加所有文件...
git add -A
echo 文件已添加到暂存区
echo.

echo [5/5] 提交并推送...
git commit -m "添加A股股票风险分析代码和报告"
echo.
echo 正在推送到GitHub...
git push -u origin main
echo.

if errorlevel 1 (
    echo.
    echo ============================================================
    echo  推送失败！可能的原因：
    echo  1. 网络问题（需要能访问GitHub）
    echo  2. 没有仓库权限
    echo  3. 远程分支名称不是main（可能是master）
    echo.
    echo  如果分支是master，请运行：
    echo  git push -u origin master
    echo ============================================================
) else (
    echo ============================================================
    echo  推送成功！
    echo  仓库地址：https://github.com/hupige/ai_quant
    echo ============================================================
)

echo.
pause
