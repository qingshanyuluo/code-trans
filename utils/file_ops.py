"""
文件读写工具 — 安全读取、带备份写入、备份恢复
"""

import os
import shutil
from config import BACKUP_SUFFIX


def read_file(path: str) -> str:
    """读取文件内容，返回字符串"""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def write_file(path: str, content: str, backup: bool = True) -> None:
    """
    写入文件内容。
    如果 backup=True，先创建 .bak 备份（仅在首次写入时备份，避免覆盖原始备份）。
    """
    if backup:
        backup_path = path + BACKUP_SUFFIX
        if not os.path.exists(backup_path) and os.path.exists(path):
            shutil.copy2(path, backup_path)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def restore_backup(path: str) -> bool:
    """
    从备份文件恢复原始内容。
    返回 True 表示恢复成功，False 表示无备份文件。
    """
    backup_path = path + BACKUP_SUFFIX
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, path)
        return True
    return False


def remove_backup(path: str) -> bool:
    """删除备份文件"""
    backup_path = path + BACKUP_SUFFIX
    if os.path.exists(backup_path):
        os.remove(backup_path)
        return True
    return False
