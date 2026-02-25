import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# 初始化 MCP 服务器
mcp = FastMCP("X2P_Clangd_Config_Parser")

def escape_yaml(s: str) -> str:
    """处理 YAML 字符串转义"""
    return s.replace('\\', '\\\\').replace('"', '\\"')

@mcp.tool()
def scan_adk_projects(root_dir: str) -> str:
    """
    扫描 ADK 根目录，返回所有可用的 .x2p 项目文件路径。
    供 Agent 在不确定目标项目时调用，以便向用户展示可用项目列表。
    """
    root_path = Path(root_dir).resolve()
    if not root_path.exists():
        return f"扫描失败：指定的根目录不存在 -> {root_path.as_posix()}"
    
    x2p_files = []
    # 遍历所有 .x2p 文件，跳过常见的无用缓存和构建目录以加速扫描
    for p in root_path.rglob('*.x2p'):
        if any(ignored in p.parts for ignored in ['.git', 'build', 'depend_']):
            continue
        x2p_files.append(p.as_posix())
        
    if not x2p_files:
        return "扫描完成：未找到任何 .x2p 文件。"
    
    res = "找到以下 .x2p 项目文件：\n"
    for idx, f in enumerate(sorted(x2p_files), 1):
        res += f"{idx}. {f}\n"
    return res

@mcp.tool()
def get_x2p_configs(x2p_file_path: str) -> str:
    """
    解析指定的 .x2p 文件，返回所有可用的配置名称（如 TRAN03H）及默认配置。
    供 Agent 询问用户激活哪个配置时提供列表支持。
    """
    x2p_path = Path(x2p_file_path).resolve()
    if not x2p_path.exists():
        return f"读取失败：找不到文件 -> {x2p_path.as_posix()}"
    
    try:
        tree = ET.parse(x2p_path)
        configs_node = tree.getroot().find('configurations')
        if configs_node is None:
            return "解析失败：未在 x2p 文件中找到 <configurations> 节点。"
        
        default_cfg = configs_node.get('default', '未指定默认值')
        cfgs = [c.get('name') for c in configs_node.findall('configuration') if c.get('name')]
        
        res = f"项目 [{x2p_path.name}] 的可用配置如下：\n"
        res += f"📌 默认配置: {default_cfg}\n\n"
        res += "📂 所有可用配置列表:\n"
        for idx, c in enumerate(cfgs, 1):
            res += f"{idx}. {c}\n"
        return res
    except Exception as e:
        return f"解析工程文件异常: {str(e)}"

@mcp.tool()
def generate_clangd_config(x2p_file_path: str = None, output_dir: str = None, config_name: str = None) -> str:
    """
    核心配置生成器：解析 x2p 生成 compile_commands.json 和 .clangd，并隔离无关子项目。
    内置智能缓存机制，仅在工程文件变更或切换项目时重新生成，并自动更新 .gitignore。
    """
    # 1. 环境变量降级与参数合并
    actual_x2p = x2p_file_path or os.environ.get("ADK_ACTIVE_X2P")
    if not actual_x2p:
        return "执行失败：未传入 x2p 路径，且系统环境变量 ADK_ACTIVE_X2P 为空。请明确指定目标工程。"

    actual_out_dir = output_dir or os.environ.get("ADK_ROOT_DIR", ".")
    actual_config = config_name or os.environ.get("ADK_ACTIVE_CONFIG")

    x2p_path = Path(actual_x2p).resolve()
    out_dir_path = Path(actual_out_dir).resolve()
    
    if not x2p_path.exists():
        return f"执行失败：找不到 .x2p 文件 -> {x2p_path.as_posix()}"

    # ==========================================
    # 🌟 智能缓存校验机制 (极速拦截)
    # ==========================================
    out_clangd = out_dir_path / ".clangd"
    out_json = out_dir_path / "compile_commands.json"
    cache_file = out_dir_path / ".x2p_parser_cache.json"
    
    current_mtime = os.path.getmtime(x2p_path)

    if out_clangd.exists() and out_json.exists() and cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if (cache_data.get("x2p_path") == x2p_path.as_posix() and 
                cache_data.get("config_name") == actual_config and 
                cache_data.get("mtime") == current_mtime):
                return f"⚡ 【缓存命中】已检测到 {x2p_path.name} (配置: {actual_config}) 未发生变更，跳过生成步骤，可直接进行代码分析。"
        except Exception:
            pass # 缓存读取失败则继续重新生成

    try:
        tree = ET.parse(x2p_path)
        root = tree.getroot()

        # 2. 确定配置节点
        configs_node = root.find('configurations')
        if not actual_config and configs_node is not None:
            actual_config = configs_node.get('default')

        target_config = None
        if configs_node is not None:
            for config in configs_node.findall('configuration'):
                if config.get('name') == actual_config:
                    target_config = config
                    break

        if target_config is None:
            return f"执行失败：找不到配置 '{actual_config}'"

        # 3. 提取宏和头文件路径
        defs, abs_incpaths = [], []
        for prop in target_config.findall('property'):
            if prop.get('name') == 'DEFS':
                defs = [d.strip() for d in (prop.text or "").split() if d.strip()]
            elif prop.get('name') == 'INCPATHS':
                abs_incpaths = [(x2p_path.parent / i.strip()).resolve() for i in (prop.text or "").split() if i.strip()]

        # 4. 提取源文件
        abs_source_files = []
        for file_node in root.iter('file'):
            path_attr = file_node.get('path')
            if path_attr and (path_attr.endswith('.c') or path_attr.endswith('.cpp')):
                abs_source_files.append((x2p_path.parent / path_attr).resolve())

        # ==========================================
        # 生成极简 compile_commands.json
        # ==========================================
        compdb = []
        for abs_src in abs_source_files:
            entry = {
                "directory": out_dir_path.as_posix(),
                "arguments": ["/usr/bin/gcc", "-c", abs_src.as_posix(), "-o", f"build/{abs_src.name}.o"],
                "file": abs_src.as_posix()
            }
            compdb.append(entry)

        out_dir_path.mkdir(parents=True, exist_ok=True)
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(compdb, f, indent=2)

        # ==========================================
        # 生成 .clangd 与动态隔离无关项目
        # ==========================================
        clangd_yaml = "CompileFlags:\n  Add:\n    - \"-xc\"\n    - \"-std=c11\"\n    - \"-Wall\"\n"
        for d in defs:
            clangd_yaml += f"    - \"-D{escape_yaml(d)}\"\n"
        for inc in abs_incpaths:
            clangd_yaml += f"    - \"-I{escape_yaml(inc.as_posix())}\"\n"

        skip_regexes = []
        for child in out_dir_path.iterdir():
            if child.is_dir() and not child.name.startswith('.'):
                is_used = any(f.is_relative_to(child) for f in abs_source_files) or \
                          any(inc.is_relative_to(child) for inc in abs_incpaths)
                if not is_used:
                    skip_regexes.append(f"{child.name}/.*")

        adk_topologies = out_dir_path / "adk" / "src" / "topologies"
        if adk_topologies.exists():
            for child in adk_topologies.iterdir():
                if child.is_dir():
                    is_used = any(f.is_relative_to(child) for f in abs_source_files) or \
                              any(inc.is_relative_to(child) for inc in abs_incpaths)
                    if not is_used:
                        rel_path = child.relative_to(out_dir_path).as_posix()
                        skip_regexes.append(f"{rel_path}/.*")

        clangd_yaml += "\nIndex:\n  Background:\n    Skip:\n"
        for regex in sorted(set(skip_regexes)):
            clangd_yaml += f"      - \"^{regex}$\"\n"

        with open(out_clangd, 'w', encoding='utf-8') as f:
            f.write(clangd_yaml)

        # ==========================================
        # 🌟 更新缓存指纹文件
        # ==========================================
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                "x2p_path": x2p_path.as_posix(),
                "config_name": actual_config,
                "mtime": current_mtime
            }, f)

        # ==========================================
        # 🌟 自动将产物加入 .gitignore
        # ==========================================
        gitignore_path = out_dir_path / ".gitignore"
        ignore_items = [".x2p_parser_cache.json", ".clangd", "compile_commands.json"]
        append_lines = []
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()
            for item in ignore_items:
                if item not in content:
                    append_lines.append(item)
            if append_lines:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    if content and not content.endswith('\n'):
                        f.write('\n')
                    f.write('\n# Auto-generated by x2p-compdb-parser MCP\n')
                    for line in append_lines:
                        f.write(f"{line}\n")
        else:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write('# Auto-generated by x2p-compdb-parser MCP\n')
                for item in ignore_items:
                    f.write(f"{item}\n")

        return (f"执行成功！(缓存与 .gitignore 已更新)\n"
                f"1. 目标工程：{x2p_path.name} (配置: {actual_config})\n"
                f"2. 成功生成/刷新了极简 {out_json.name} 与 {out_clangd.name}，并屏蔽了 {len(skip_regexes)} 个无关项目目录。")

    except Exception as e:
        return f"解析过程发生异常: {str(e)}"

if __name__ == "__main__":
    mcp.run()