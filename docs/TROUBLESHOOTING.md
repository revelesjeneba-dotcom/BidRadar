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

V6.6 安全写入接入后的行为：

- Excel 无法读取时脚本停止，不会用空表覆盖历史。
- 写入先生成同目录临时文件，验证成功后才替换目标。
- 已有文件的自动备份位于 `backup/auto/<文件名>/`。
- 写入失败时先确认原文件是否仍可读取，再查看对应自动备份。

## TXT 安全写入

`daily_report.txt` 和 `eia_diagnosis.txt` 使用 UTF-8 临时文件、回读校验、
自动备份和原子替换。备份位于 `backup/auto/<文件名>/`。

如果文本写入失败：

- 不要删除原 TXT；失败流程会优先保留或恢复旧文件。
- 检查文件是否被编辑器占用、目标目录是否可写。
- 检查 `backup/auto/daily_report/` 或 `backup/auto/eia_diagnosis/`。
- 自动恢复失败时，将最新备份复制回原文件位置，并用 UTF-8 打开核对。

## Git

现象：`git status` 显示 Excel/TXT 被修改。

处理：

- 先确认是否由脚本运行造成。
- 不要随意还原未确认的数据文件。
- 文档、代码、数据文件建议分开提交。

## 发布回归

推荐命令：

```bash
.venv/bin/python -B -m unittest discover -s tests -v
```

- 该测试集使用临时目录、mock 和网络阻断，不应修改项目根目录的正式 Excel/TXT。
- 静态语法检查应使用内存 `compile()`，避免生成 `__pycache__`。
- 跨目录启动验证应在独立 Python 进程中设置项目导入路径后导入 `paths`；不要依赖修改后的当前工作目录重新加载模块。
- 发布前后如正式数据哈希不同，立即停止提交，先确认变更来源，不要直接还原未确认的数据。

## 常见错误

- 运行 `main.py` 意外联网：检查 `USE_SAMPLE_DATA`。
- 日报写入失败：检查 `backup/auto/daily_report/` 中的最新备份。
- 调试文件写入失败：保留原文件，检查对应 `backup/auto/<文件名>/` 备份和异常信息。
- 状态表字段变化：确认是否运行了跟进、客户池或企业验证脚本。
