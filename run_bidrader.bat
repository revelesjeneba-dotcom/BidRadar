@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 正在运行纸箱招标雷达系统
echo ========================================
echo.

python main.py

echo.
echo ========================================
echo 运行完成，请查看 bid_results.xlsx 和 daily_report.txt
echo ========================================
echo.
pause
