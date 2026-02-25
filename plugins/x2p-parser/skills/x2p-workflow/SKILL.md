---
name: adk-x2p-c-analyzer-workflow
description: |
  Essential workflow for analyzing, refactoring, or querying C/C++ code in Qualcomm ADK projects.
  当用户要求分析、阅读、重构 C/C++ 代码，或者询问底层架构、PIO 宏定义等问题时，请自动触发此技能。
---

# 高通 ADK 代码分析与重构工作流

高通 ADK 是一个庞大的 Monorepo，包含了 headset、earbuds 等多个相互平行的子项目。为了避免不同项目的同名符号（如 `main` 或 `app_sm`）在代码分析时产生冲突（符号污染），并消除配置冗余，你必须严格按顺序执行以下 Workflow：

### 第 0 步：跨平台路径对其预检
执行系统命令（如 `uname -a`）判断当前运行环境。如果你在 WSL 中，但项目存储在 Windows 盘符，必须使用 `/mnt/c/` 等形式的绝对路径，绝对禁止向后续工具传入带有反斜杠 `\` 的路径。

### 第 1 步：环境同步与动态隔离 (调用 x2p 解析工具)
调用本插件自带的 `generate_optimized_clangd_config` 工具。
- `x2p_file_path`：传入当前需要分析的 `.x2p` 文件的绝对路径。
- `output_dir`：传入 ADK 项目根目录的绝对路径。
- `config_name`：留空，让工具自动读取默认配置。

*(提示：该工具运用了先进的分层架构，会生成极简的 `compile_commands.json` 锁定项目文件，并生成 `.clangd` 全局注入宏定义且动态生成正则表达式屏蔽无关子项目的目录)*

### 第 2 步：防崩检查 (Sanity Check)
检查项目根目录下是否成功生成了 `.clangd` 和 `compile_commands.json`。
使用 `cat .clangd` 检查底部的 `Skip:` 列表，确保包含正斜杠路径。若发现反斜杠导致路径异常，使用 `sed` 修复。

### 第 3 步：符号解析 (调用 Serena)
配置就绪后，调用 `serena` MCP 进行深度的代码检索和结构分析。此时 Serena 底层的 clangd 能够在几毫秒内极速加载配置，并被牢牢“锁定”在当前 x2p 所定义的源码范围内。