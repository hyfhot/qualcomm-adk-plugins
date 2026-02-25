import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("X2P_Clangd_Config_Parser")

def escape_yaml(s: str) -> str:
    """处理 YAML 字符串转义"""
    return s.replace('\\', '\\\\').replace('"', '\\"')

@mcp.tool()
def generate_optimized_clangd_config(x2p_file_path: str, output_dir: str, config_name: str = None) -> str:
    """
    解析高通 ADK 的 .x2p 工程文件，生成极简无冗余的 compile_commands.json，
    并动态生成 .clangd 文件以全局注入宏定义，同时精准隔离/屏蔽无关的 ADK 子项目源码。
    """
    x2p_path = Path(x2p_file_path).resolve()
    out_dir = Path(output_dir).resolve()
    
    if not x2p_path.exists():
        return f"执行失败：找不到 .x2p 文件 -> {x2p_path.as_posix()}"

    try:
        tree = ET.parse(x2p_path)
        root = tree.getroot()

        # 1. 确定配置节点
        configs_node = root.find('configurations')
        if not config_name and configs_node is not None:
            config_name = configs_node.get('default')

        target_config = None
        if configs_node is not None:
            for config in configs_node.findall('configuration'):
                if config.get('name') == config_name:
                    target_config = config
                    break

        if target_config is None:
            return f"执行失败：找不到配置 '{config_name}'"

        # 2. 提取宏和头文件路径 (转换为绝对路径 Path 对象)
        defs = []
        abs_incpaths = []
        for prop in target_config.findall('property'):
            if prop.get('name') == 'DEFS':
                defs = [d.strip() for d in (prop.text or "").split() if d.strip()]
            elif prop.get('name') == 'INCPATHS':
                # 直接将解析到的相对 include 路径转换为绝对路径
                abs_incpaths = [(x2p_path.parent / i.strip()).resolve() for i in (prop.text or "").split() if i.strip()]

        # 3. 提取源文件并转为绝对路径
        abs_source_files = []
        for file_node in root.iter('file'):
            path_attr = file_node.get('path')
            if path_attr and (path_attr.endswith('.c') or path_attr.endswith('.cpp')):
                abs_source_files.append((x2p_path.parent / path_attr).resolve())

        # ==========================================
        # 优化 A：生成极简版 compile_commands.json
        # ==========================================
        compdb = []
        for abs_src in abs_source_files:
            entry = {
                "directory": out_dir.as_posix(),
                # 只有裸命令，没有任何宏和头文件，极致缩减体积
                "arguments": ["/usr/bin/gcc", "-c", abs_src.as_posix(), "-o", f"build/{abs_src.name}.o"],
                "file": abs_src.as_posix()
            }
            compdb.append(entry)

        out_dir.mkdir(parents=True, exist_ok=True)
        out_json = out_dir / "compile_commands.json"
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(compdb, f, indent=2)

        # ==========================================
        # 优化 B：生成动态 .clangd 文件 (全局注入 + 精准隔离)
        # ==========================================
        clangd_yaml = "CompileFlags:\n  Add:\n    - \"-xc\"\n    - \"-std=c11\"\n    - \"-Wall\"\n"
        for d in defs:
            clangd_yaml += f"    - \"-D{escape_yaml(d)}\"\n"
        for inc in abs_incpaths:
            clangd_yaml += f"    - \"-I{escape_yaml(inc.as_posix())}\"\n"

        # 动态计算需要 Skip（屏蔽）的无关目录
        skip_regexes = []
        
        # 遍历输出目录下的顶层目录
        for child in out_dir.iterdir():
            if child.is_dir() and not child.name.startswith('.'):
                # 核心修正：一个目录是否被“使用”，取决于它是否包含源文件，或者它是否被包含在 INCPATHS 中
                contains_source = any(f.is_relative_to(child) for f in abs_source_files)
                contains_include = any(inc.is_relative_to(child) for inc in abs_incpaths)
                
                is_used = contains_source or contains_include
                
                if not is_used:
                    skip_regexes.append(f"{child.name}/.*")

        # 针对 ADK topologies 目录进行深度隔离 (进一步屏蔽无关的子拓扑如 earbud 等)
        adk_topologies = out_dir / "adk" / "src" / "topologies"
        if adk_topologies.exists():
            for child in adk_topologies.iterdir():
                if child.is_dir():
                    contains_source = any(f.is_relative_to(child) for f in abs_source_files)
                    contains_include = any(inc.is_relative_to(child) for inc in abs_incpaths)
                    
                    is_used = contains_source or contains_include
                    
                    if not is_used:
                        rel_path = child.relative_to(out_dir).as_posix()
                        skip_regexes.append(f"{rel_path}/.*")

        clangd_yaml += "\nIndex:\n  Background:\n    Skip:\n"
        # 去重并写入正则表达式
        for regex in sorted(set(skip_regexes)):
            clangd_yaml += f"      - \"^{regex}$\"\n"

        out_clangd = out_dir / ".clangd"
        with open(out_clangd, 'w', encoding='utf-8') as f:
            f.write(clangd_yaml)

        return (f"执行成功！\n"
                f"1. 生成极简 {out_json.name}，包含 {len(compdb)} 个文件，已彻底剔除重复冗余。\n"
                f"2. 生成 {out_clangd.name}，全局注入 {len(defs)} 个宏和 {len(abs_incpaths)} 个包含路径。\n"
                f"3. 动态计算排除名单：通过交叉比对源文件与 INCPATHS，已安全屏蔽 {len(skip_regexes)} 个无关项目目录（如其它 application 或未引用的 topologies）。")

    except Exception as e:
        return f"解析过程发生异常: {str(e)}"

if __name__ == "__main__":
    mcp.run()