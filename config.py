"""
全局配置模块
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# LLM 配置
# ============================================================
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

# ============================================================
# 迁移配置
# ============================================================
MAX_RETRY_COUNT = int(os.getenv("MAX_RETRY_COUNT", "3"))

# ============================================================
# 文件配置
# ============================================================
MIGRATION_PLAN_FILENAME = "MIGRATION_PLAN.md"
BACKUP_SUFFIX = ".bak"
SUPPORTED_EXTENSIONS = [
    ".py",
    ".js", ".ts", ".jsx", ".tsx",
    ".vue", ".svelte",
    ".java", ".kt",
    ".go", ".rs",
    ".rb", ".php",
    ".css", ".scss", ".less",
    ".html",
]

# ============================================================
# 验证配置
# ============================================================
PYTHON_EXECUTABLE = os.getenv("PYTHON_EXECUTABLE", "python3")
USE_RUFF_LINTER = os.getenv("USE_RUFF_LINTER", "false").lower() == "true"
