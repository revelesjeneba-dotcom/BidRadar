# Troubleshooting

## Windows 权限

现象：运行 Python 编译或脚本时出现 `PermissionError` 或 `[WinError 5]`。

处理：

- 优先使用 `python -B`，避免写入 `__pycache__`。
- 确认没有编辑器、杀毒软件或同步工具锁定目录。
- 避免在受限目录外写文件。

## Playwright

现象：`jianyu_search.py` 提示 Playwright 未安装或找不到 Chromium。

处理：

- 确认是否允许安装依赖和浏览器。
- 安装前记录命令和结果。
- Playwright 脚本会访问外部网站，运行前必须确认。

## __pycache__

现象：静态编译尝试写入 `__pycache__` 失败。

处理：

- 使用 `python -B script.py`。
- 或使用不写字节码的静态 `compile()` 检查。
- 不要因为该错误修改业务代码。

## UTF-8

现象：中文输出乱码。

处理：

- PowerShell 读取文件时使用 `-Encoding UTF8`。
- Python 脚本中已有部分 stdout UTF-8 reconfigure。
- 文档统一使用 UTF-8。

## Excel 锁定

现象：写 Excel 失败、权限被拒绝、保存失败。

处理：

- 关闭正在打开的 Excel 文件。
- 确认没有其他脚本正在写同一文件。
- 对 `customer_pool.xlsx` 和 `enterprise_url_status.xlsx` 这类共享状态表，运行前优先备份。

## Git

现象：`git status` 显示 Excel/TXT 被修改。

处理：

- 先确认是否由脚本运行造成。
- 不要随意还原未确认的数据文件。
- 文档、代码、数据文件建议分开提交。

## 常见错误

- 运行 `main.py` 意外联网：检查 `USE_SAMPLE_DATA`。
- 日报被覆盖：`reporter.py` 会直接写 `daily_report.txt`。
- 调试文件被覆盖：debug 脚本多为直接写回。
- 状态表字段变化：确认是否运行了跟进、客户池或企业验证脚本。
