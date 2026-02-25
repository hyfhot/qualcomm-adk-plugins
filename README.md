# Qualcomm ADK Plugins

高通 ADK 开发专属 Claude Code 插件市场，为 Qualcomm ADK (Audio Development Kit) 项目提供智能代码分析与重构能力。

## 插件列表

### x2p-compdb-parser

自动解析高通 `.x2p` 工程文件，并跨平台为 Serena/clangd 生成 `compile_commands.json` 的智能插件。

**核心功能：**
- 解析 `.x2p` 工程配置文件，提取宏定义和头文件路径
- 生成极简版 `compile_commands.json`，消除冗余
- 动态生成 `.clangd` 文件，全局注入宏定义
- 智能屏蔽无关 ADK 子项目，避免符号污染

## 快速开始

### 前置要求

- Claude Code
- Python 3.10+
- `uv` 包管理器

### 安装

1. 克隆仓库：
```bash
git clone https://github.com/your-repo/qualcomm-adk-plugins.git
cd qualcomm-adk-plugins
```

2. 在 Claude Code 中加载插件：
- 将 `plugins/x2p-parser` 目录配置为你的 Claude Code 插件路径

### 使用

#### 方式一：直接调用 MCP 工具

```python
# 调用 generate_optimized_clangd_config 工具
x2p_file_path = "/path/to/project.x2p"
output_dir = "/path/to/adk/root"
config_name = None  # 使用默认配置
```

#### 方式二：使用工作流技能

当分析 ADK C/C++ 代码时，工作流会自动：
1. 检测运行环境（跨平台路径处理）
2. 调用 x2p 解析工具生成配置
3. 执行防崩检查
4. 调用 Serena 进行深度代码分析

## 项目结构

```
qualcomm-adk-plugins/
├── .claude-plugin/
│   └── marketplace.json          # 插件市场配置
└── plugins/
    └── x2p-parser/
        ├── .claude-plugin/
        │   └── plugin.json       # 插件元数据
        ├── .mcp.json              # MCP 服务配置
        ├── scripts/
        │   └── x2p_compdb_mcp.py # 核心解析脚本
        └── skills/
            └── x2p-workflow/
                └── SKILL.md      # ADK 代码分析工作流
```

## 技术原理

### 极简 compile_commands.json

传统方式会将所有宏和头文件路径写入每条编译命令，导致文件体积庞大。本插件采用分层架构：
- `compile_commands.json`：仅包含文件列表，无冗余
- `.clangd`：全局注入宏定义和头文件路径

### 智能目录隔离

ADK 是庞大的 Monorepo，包含 headset、earbuds 等多个子项目。通过分析源文件与 INCPATHS 的关系，动态生成 Skip 正则表达式，屏蔽无关项目，避免符号冲突。

## 相关文档

- [高通 ADK 官方文档](https://developer.qualcomm.com/)
- [Clangd 配置](https://clangd.llvm.org/config.html)
- [Claude Code 插件开发](https://docs.anthropic.com/en/docs/claude-code/plugins)

## License

MIT License
