"""
验证器工具 — 语言感知的编译检查、Lint 检查
"""

import os
import subprocess
from config import PYTHON_EXECUTABLE, USE_RUFF_LINTER


# 按文件扩展名分派编译检查策略
_COMPILE_STRATEGIES = {
    ".py": "python",
    ".js": "node",
    ".ts": "node",
    ".jsx": "node",
    ".tsx": "node",
}


def compile_check(file_path: str) -> tuple[bool, str]:
    """
    根据文件类型选择编译/语法检查方式。
    - .py  → python -m py_compile
    - .js  → node --check
    - 其他 → 跳过（默认通过）
    """
    ext = os.path.splitext(file_path)[1].lower()
    strategy = _COMPILE_STRATEGIES.get(ext)

    if strategy == "python":
        return _python_compile(file_path)
    elif strategy == "node":
        return _node_check(file_path)
    else:
        return True, ""


def _python_compile(file_path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, "-m", "py_compile", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        error = result.stderr.strip() or result.stdout.strip()
        return False, error
    except subprocess.TimeoutExpired:
        return False, "编译检查超时"
    except FileNotFoundError:
        return False, f"找不到 Python 解释器: {PYTHON_EXECUTABLE}"


def _node_check(file_path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["node", "--check", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        error = result.stderr.strip() or result.stdout.strip()
        return False, error
    except FileNotFoundError:
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Node 语法检查超时"


def lint_check(file_path: str) -> tuple[bool, str]:
    """
    运行 ruff 进行 lint 检查（仅 .py 文件，且需开启配置）。
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext != ".py" or not USE_RUFF_LINTER:
        return True, ""

    try:
        result = subprocess.run(
            ["ruff", "check", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        output = result.stdout.strip() or result.stderr.strip()
        return False, output
    except FileNotFoundError:
        return True, "ruff 未安装，跳过 lint 检查"
    except subprocess.TimeoutExpired:
        return False, "Lint 检查超时"


def validate_file(file_path: str) -> dict:
    """
    聚合验证结果。
    """
    compile_ok, compile_error = compile_check(file_path)
    lint_ok, lint_error = lint_check(file_path)

    return {
        "file": file_path,
        "compile_ok": compile_ok,
        "compile_error": compile_error,
        "lint_ok": lint_ok,
        "lint_error": lint_error,
        "success": compile_ok and lint_ok,
    }
