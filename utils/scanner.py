"""
文件扫描工具 — 项目扫描、grep 搜索、项目概要生成
"""

import os
import re
import subprocess
from config import SUPPORTED_EXTENSIONS


def scan_project(project_path: str) -> list[str]:
    """递归获取项目中所有支持的源文件路径列表"""
    files = []
    for root, _dirs, filenames in os.walk(project_path):
        _dirs[:] = [
            d for d in _dirs
            if not d.startswith('.')
            and d not in ('__pycache__', '.venv', 'venv', 'node_modules', 'dist', 'build')
        ]
        for fname in filenames:
            if any(fname.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                files.append(os.path.join(root, fname))
    return sorted(files)


def grep_pattern(project_path: str, pattern: str) -> list[dict]:
    """
    在项目中搜索匹配指定正则模式的文件和行。

    返回: [{"file": str, "line_number": int, "content": str}, ...]
    """
    matches = []
    regex = re.compile(pattern)

    for filepath in scan_project(project_path):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        matches.append({
                            "file": filepath,
                            "line_number": i,
                            "content": line.rstrip('\n'),
                        })
        except (IOError, OSError):
            continue

    return matches


def grep_files_with_pattern(project_path: str, pattern: str) -> list[str]:
    """返回包含指定正则模式的文件路径列表（去重）"""
    matches = grep_pattern(project_path, pattern)
    seen = set()
    result = []
    for m in matches:
        if m["file"] not in seen:
            seen.add(m["file"])
            result.append(m["file"])
    return result


def get_project_summary(project_path: str) -> str:
    """
    生成项目概要信息，供 Planner Agent 使用。
    包含：文件列表、依赖文件内容、各文件前20行内容。
    """
    files = scan_project(project_path)
    lines = []
    lines.append(f"## 项目路径: {project_path}")
    lines.append(f"## 源文件数量: {len(files)}")
    lines.append("")

    # 检查依赖文件
    dep_candidates = [
        "requirements.txt", "setup.py", "pyproject.toml", "Pipfile",
        "package.json", "pom.xml", "build.gradle", "Cargo.toml", "go.mod",
        "Gemfile", "composer.json",
    ]
    for dep_file in dep_candidates:
        dep_path = os.path.join(project_path, dep_file)
        if os.path.exists(dep_path):
            lines.append(f"### 依赖文件: {dep_file}")
            lines.append("```")
            with open(dep_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines.append(f.read().strip())
            lines.append("```")
            lines.append("")

    _EXT_LANG = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "jsx", ".tsx": "tsx", ".vue": "vue", ".svelte": "svelte",
        ".java": "java", ".kt": "kotlin", ".go": "go", ".rs": "rust",
        ".rb": "ruby", ".php": "php", ".css": "css", ".scss": "scss",
        ".less": "less", ".html": "html", ".json": "json",
    }

    lines.append("### 文件列表与内容预览")
    for filepath in files:
        rel_path = os.path.relpath(filepath, project_path)
        ext = os.path.splitext(filepath)[1].lower()
        lang = _EXT_LANG.get(ext, "")
        lines.append(f"\n#### {rel_path}")
        lines.append(f"```{lang}")
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines.append(f.read())
        except (IOError, OSError):
            lines.append("// [无法读取]")
        lines.append("```")

    return "\n".join(lines)
