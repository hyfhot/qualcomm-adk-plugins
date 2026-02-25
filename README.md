# Qualcomm ADK Plugins

高通 ADK 开发专属 Claude Code 插件市场，为 Qualcomm ADK (Audio Development Kit) 项目提供智能代码分析与重构能力。

## 插件列表

### x2p-compdb-parser (v2.0.0)

自动解析高通 `.x2p` 工程文件，具备项目扫描、交互式配置提取，并为 Serena/clangd 生成极简配置的智能跨平台插件。

**核心功能：**
- **项目扫描** (`scan_adk_projects`) - 自动扫描 ADK 根目录，列出所有可用 .x2p 项目
- **配置提取** (`get_x2p_configs`) - 解析 .x2p 文件，获取所有可用配置名称（如 TRAN03H）
- **智能缓存** - 内置极速缓存校验机制，仅在工程文件变更时重新生成
- **自动忽略** - 自动将生成的配置文件加入 .gitignore
- **环境变量支持** - 支持通过 ADK_ACTIVE_X2P、ADK_ACTIVE_CONFIG 环境变量配置
- **极简配置** - 生成极简版 compile_commands.json，消除冗余
- **动态隔离** - 智能屏蔽无关 ADK 子项目，避免符号污染

---

## 快速开始

### 前置要求

- Claude Code
- Python 3.10+
- `uv` 包管理器

### 安装

本插件支持两种安装方式：

#### 方式一：通过插件市场安装（推荐）

如果您的 Claude Code 已配置插件市场，可以直接从市场安装：

1. 在 Claude Code 中运行命令添加插件源：
```bash
# 克隆仓库
git clone https://github.com/hyfhot/qualcomm-adk-plugins.git
cd qualcomm-adk-plugins
```

2. 将插件配置路径添加到 Claude Code 设置中：
   - 打开 Claude Code 设置
   - 找到「插件/Plugins」配置项
   - 添加插件目录路径：`./qualcomm-adk-plugins/plugins/x2p-parser`

#### 方式二：手动安装

1. 克隆仓库：
```bash
git clone https://github.com/hyfhot/qualcomm-adk-plugins.git
cd qualcomm-adk-plugins
```

2. 复制插件目录到 Claude Code 插件目录：
```bash
# 方式A：将整个仓库作为插件源
# 在 Claude Code 设置中添加: ./qualcomm-adk-plugins/plugins/x2p-parser
cp -r plugins/x2p-parser ~/.claude/plugins/x2p-parser
```

---

## 插件启用

插件安装后，需要在 Claude Code 中启用：

1. **重启 Claude Code**：安装新插件后需要重启使配置生效

2. **验证插件状态**：
```bash
# 检查插件是否加载成功
# 在 Claude Code 中输入:
/plugins list
```

3. **MCP 服务自动启动**：
   - 插件包含 `.mcp.json` 配置文件
   - Claude Code 启动时会自动运行 `uv run --with mcp x2p_compdb_mcp.py`
   - MCP 服务启动后，您可以使用 `generate_clangd_config` 工具

---

## 插件禁用

如需临时禁用插件，有以下几种方式：

### 方式一：修改插件设置

1. 打开 Claude Code 设置
2. 找到「插件/Plugins」配置项
3. 移除或注释掉插件路径：
   ```json
   // 注释掉或删除此行
   // "./qualcomm-adk-plugins/plugins/x2p-parser"
   ```

### 方式二：重命名插件目录

```bash
# 在插件目录名后添加 .disabled 后缀
mv ~/.claude/plugins/x2p-parser ~/.claude/plugins/x2p-parser.disabled
```

### 方式三：删除 MCP 配置

直接删除或重命名 `.mcp.json` 文件：
```bash
mv ~/.claude/plugins/x2p-parser/.mcp.json ~/.claude/plugins/x2p-parser/.mcp.json.disabled
```

**注意**：禁用后需要重启 Claude Code 才能生效。

---

## 插件卸载

完全卸载插件的步骤：

1. **删除插件目录**：
```bash
rm -rf ~/.claude/plugins/x2p-parser
# 或删除整个仓库
rm -rf qualcomm-adk-plugins
```

2. **清理生成的配置文件**（可选）：
```bash
# 如果之前运行过插件，会在 ADK 项目目录下生成以下文件
# 这些文件可以手动删除
rm -f /path/to/adk/project/.clangd
rm -f /path/to/adk/project/compile_commands.json
```

3. **重启 Claude Code**：
   卸载后需要重启 Claude Code 使更改生效。

---

## 使用教程

### 方式一：直接调用 MCP 工具

插件提供三个 MCP 工具：

#### 1. scan_adk_projects - 扫描项目
扫描 ADK 根目录，返回所有可用的 `.x2p` 项目文件路径。

```python
root_dir = "/path/to/adk/root"
```

#### 2. get_x2p_configs - 获取配置
解析指定的 `.x2p` 文件，返回所有可用的配置名称。

```python
x2p_file_path = "/path/to/project.x2p"
```

#### 3. generate_clangd_config - 生成配置（核心）
解析 x2p 生成 compile_commands.json 和 .clangd，并隔离无关子项目。

```python
# 方式A：直接传参
x2p_file_path = "/path/to/project.x2p"
output_dir = "/path/to/adk/root"
config_name = None  # 使用默认配置

# 方式B：通过环境变量（推荐）
# 设置环境变量后无需传参
# ADK_ACTIVE_X2P=/path/to/project.x2p
# ADK_ROOT_DIR=/path/to/adk/root
# ADK_ACTIVE_CONFIG=TRAN03H
```

**参数说明：**
- `x2p_file_path`：`.x2p` 工程文件的绝对路径（支持环境变量 ADK_ACTIVE_X2P）
- `output_dir`：ADK 项目根目录的绝对路径（支持环境变量 ADK_ROOT_DIR）
- `config_name`：配置名称（支持环境变量 ADK_ACTIVE_CONFIG）

### 方式二：使用工作流技能

当分析 ADK C/C++ 代码时，工作流会自动：
1. **项目指纹确认** - 快速检测是否为高通 ADK 项目
2. **跨平台路径处理** - WSL/Windows 路径转换
3. **交互式选择** - 扫描并让用户选择目标项目和配置
4. **环境同步** - 调用解析工具生成配置（含智能缓存）
5. **符号解析** - 调用 Serena 进行深度代码分析

**触发条件**：当用户要求分析、阅读、重构 C/C++ 代码，且项目包含 `adk/`、`application_common/` 等高通特征目录时自动触发。

---

## 生成内容详解

### 工作原理

本插件采用分层架构 + 智能缓存解决 ADK 项目代码分析的难题：

#### 1. 极简 compile_commands.json

传统方式会将所有宏和头文件路径写入每条编译命令，导致文件体积庞大（通常 10MB+）。本插件采用分层架构：

```
compile_commands.json：仅包含文件列表，无冗余
.clangd：全局注入宏定义和头文件路径
```

**优化效果**：
- 文件体积减少 95%+
- clangd 启动速度提升 10 倍+

#### 2. 智能缓存机制

插件内置极速缓存校验：
- 首次生成后创建 `.x2p_parser_cache.json` 缓存文件
- 再次调用时自动检测 x2p 文件的修改时间 (mtime)
- 若文件未变更，直接返回 "缓存命中"，跳过生成步骤
- 确保每次分析前环境同步，同时避免重复计算

#### 3. 自动 .gitignore 管理

插件自动将生成的配置文件加入 .gitignore：
- `.clangd`
- `compile_commands.json`
- `.x2p_parser_cache.json`

#### 2. 动态 .clangd 配置

插件会解析 `.x2p` 文件，提取以下信息：

- **DEFS**：宏定义（如 `-DDEBUG=1`）
- **INCPATHS**：头文件搜索路径
- **源文件列表**：需要分析的 `.c` / `.cpp` 文件

然后生成 `.clangd` 文件：
```yaml
CompileFlags:
  Add:
    - "-xc"
    - "-std=c11"
    - "-Wall"
    - "-DDEBUG=1"           # 从 DEFS 提取
    - "-D__ADK__"           # 从 DEFS 提取
    - "-I/path/to/include"  # 从 INCPATHS 提取
    - ...

Index:
  Background:
    Skip:
      - "^earbuds/.*"       # 智能屏蔽无关项目
      - "^headset/.*"       # 动态计算排除名单
```

#### 3. 智能目录隔离

ADK 是庞大的 Monorepo，包含 headset、earbuds、speakers 等多个子项目。通过分析源文件与 INCPATHS 的关系，动态生成 Skip 正则表达式：

- 自动检测哪些子项目被当前 `.x2p` 使用
- 屏蔽未使用的项目避免符号冲突
- 支持 topologies 目录深度隔离

**算法流程**：
```
1. 遍历 ADK 根目录下所有顶层目录
2. 检查目录是否包含源文件（在 compile_commands.json 中）
3. 检查目录是否在 INCPATHS 中
4. 如果既不含源文件也不在包含路径中 → 加入 Skip 列表
5. 特别处理 adk/src/topologies 目录进行深度隔离
```

### 输出示例

#### 首次生成
```
执行成功！(缓存与 .gitignore 已更新)
1. 目标工程：headset.x2p (配置: TRAN03H)
2. 成功生成/刷新了极简 compile_commands.json 与 .clangd，并屏蔽了 3 个无关项目目录。
```

#### 缓存命中（极速跳过）
```
⚡ 【缓存命中】已检测到 headset.x2p (配置: TRAN03H) 未发生变更，跳过生成步骤，可直接进行代码分析。
```

---

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

### 核心文件说明

| 文件 | 说明 |
|------|------|
| `plugin.json` | 插件元数据（名称、版本、描述） |
| `.mcp.json` | MCP 服务器配置，定义工具入口 |
| `x2p_compdb_mcp.py` | 核心 Python 脚本，实现三个 MCP 工具 |
| `SKILL.md` | Claude Code 技能定义（交互式工作流） |

### MCP 工具清单

| 工具名 | 功能 |
|--------|------|
| `scan_adk_projects` | 扫描 ADK 根目录，返回所有 .x2p 项目 |
| `get_x2p_configs` | 解析 .x2p 文件，返回可用配置列表 |
| `generate_clangd_config` | 核心配置生成器（含缓存） |

---

## 技术原理

### 为什么需要这个插件？

1. **符号污染问题**：ADK 多个子项目有同名符号（如 `main`、`app_sm`），直接分析会产生冲突
2. **配置冗余问题**：`compile_commands.json` 体积过大，clangd 加载缓慢
3. **跨平台问题**：Windows 路径需要转换为 WSL 路径格式
4. **交互选择问题**：多项目多配置需要手动指定

### 分层架构优势

| 层级 | 职责 | 优势 |
|------|------|------|
| compile_commands.json | 文件列表 | 极简体积，快速加载 |
| .clangd | 宏定义+路径注入 | 全局生效，动态隔离 |
| 缓存机制 | 变更检测 | 极速跳过，避免重复计算 |
| 技能工作流 | 自动化流程 | 无需手动配置，交互式选择 |

---

## 相关文档

- [高通 ADK 官方文档](https://developer.qualcomm.com/)
- [Clangd 配置](https://clangd.llvm.org/config.html)
- [Claude Code 插件开发](https://docs.anthropic.com/en/docs/claude-code/plugins)
- [MCP 协议文档](https://modelcontextprotocol.io/)

---

## License

MIT License
