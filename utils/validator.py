"""
验证器工具 — 编译检查、Lint 检查
"""

import subprocess
import sys
from config import PYTHON_EXECUTABLE, USE_RUFF_LINTER


def compile_check(file_path: str) -> tuple[bool, str]:
    """
    运行 python -m py_compile 检查文件语法。

    返回: (success: bool, error_output: str)
    """
    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, "-m", "py_compile", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        else:
            error = result.stderr.strip() or result.stdout.strip()
            return False, error
    except subprocess.TimeoutExpired:
        return False, "编译检查超时"
    except FileNotFoundError:
        return False, f"找不到 Python 解释器: {PYTHON_EXECUTABLE}"


def lint_check(file_path: str) -> tuple[bool, str]:
    """
    运行 ruff 进行 lint 检查（可选）。

    返回: (success: bool, lint_output: str)
    """
    if not USE_RUFF_LINTER:
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
        else:
            output = result.stdout.strip() or result.stderr.strip()
            return False, output
    except FileNotFoundError:
        return True, "ruff 未安装，跳过 lint 检查"
    except subprocess.TimeoutExpired:
        return False, "Lint 检查超时"


def validate_file(file_path: str) -> dict:
    """
    聚合验证结果。

    返回: {
        "file": str,
        "compile_ok": bool,
        "compile_error": str,
        "lint_ok": bool,
        "lint_error": str,
        "success": bool
    }
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
