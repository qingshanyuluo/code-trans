"""
MIGRATION_PLAN.md 解析器 — 解析、更新任务状态
"""

import os
import re
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class Task:
    """一个迁移任务"""
    id: str                     # e.g. "1.1"
    description: str            # 任务描述文本
    status: str                 # "pending" | "in_progress" | "done" | "blocked"
    phase: str = ""             # 所属阶段名称
    line_number: int = 0        # 在文件中的行号（用于更新）


@dataclass
class Phase:
    """一个迁移阶段"""
    name: str
    tasks: List[Task] = field(default_factory=list)


# 状态标记映射
STATUS_MARKERS = {
    "pending": "- [ ]",
    "in_progress": "- [/]",
    "done": "- [x]",
    "blocked": "- [Blocked]",
}

# 反向映射：从标记到状态
MARKER_TO_STATUS = {
    "[ ]": "pending",
    "[/]": "in_progress",
    "[x]": "done",
    "[Blocked]": "blocked",
}


def parse_plan(plan_path: str) -> List[Phase]:
    """
    解析 MIGRATION_PLAN.md，返回结构化的阶段/任务列表。
    """
    if not os.path.exists(plan_path):
        return []

    with open(plan_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    phases = []
    current_phase = None
    # 匹配阶段标题: ## 阶段 1：xxx  或 ## Phase 1: xxx
    phase_pattern = re.compile(r'^##\s+(.+)$')
    # 匹配任务行: - [ ] 任务 1.1：xxx  或 - [x] 任务 1.1：xxx
    task_pattern = re.compile(
        r'^-\s+\[([ x/]|Blocked)\]\s+任务\s+(\d+\.\d+)[：:]\s*(.+)$'
    )

    for i, line in enumerate(lines):
        line_stripped = line.rstrip('\n')

        phase_match = phase_pattern.match(line_stripped)
        if phase_match:
            current_phase = Phase(name=phase_match.group(1).strip())
            phases.append(current_phase)
            continue

        task_match = task_pattern.match(line_stripped)
        if task_match and current_phase is not None:
            marker = task_match.group(1)
            task_id = task_match.group(2)
            description = task_match.group(3).strip()

            if marker == " ":
                status = "pending"
            elif marker == "/":
                status = "in_progress"
            elif marker == "x":
                status = "done"
            elif marker == "Blocked":
                status = "blocked"
            else:
                status = "pending"

            task = Task(
                id=task_id,
                description=description,
                status=status,
                phase=current_phase.name,
                line_number=i,
            )
            current_phase.tasks.append(task)

    return phases


def update_task_status(plan_path: str, task_id: str, new_status: str) -> bool:
    """
    更新 MIGRATION_PLAN.md 中指定任务的状态。

    new_status: "pending" | "in_progress" | "done" | "blocked"
    返回: True 表示更新成功
    """
    if not os.path.exists(plan_path):
        return False

    with open(plan_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    task_pattern = re.compile(
        r'^(-\s+\[)([ x/]|Blocked)(\]\s+任务\s+' + re.escape(task_id) + r'[：:])'
    )

    status_char_map = {
        "pending": " ",
        "in_progress": "/",
        "done": "x",
        "blocked": "Blocked",
    }

    updated = False
    for i, line in enumerate(lines):
        match = task_pattern.match(line)
        if match:
            new_char = status_char_map.get(new_status, " ")
            lines[i] = f"{match.group(1)}{new_char}{match.group(3)}{line[match.end():]}"
            updated = True
            break

    if updated:
        with open(plan_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return updated


def get_next_pending_task(plan_path: str) -> Optional[Task]:
    """获取下一个未完成（pending）的任务"""
    phases = parse_plan(plan_path)
    for phase in phases:
        for task in phase.tasks:
            if task.status == "pending":
                return task
    return None


def get_all_pending_tasks(plan_path: str) -> List[Task]:
    """获取所有未完成的任务"""
    phases = parse_plan(plan_path)
    pending = []
    for phase in phases:
        for task in phase.tasks:
            if task.status == "pending":
                pending.append(task)
    return pending


def get_progress_summary(plan_path: str) -> str:
    """获取进度摘要"""
    phases = parse_plan(plan_path)
    total = 0
    done = 0
    blocked = 0
    for phase in phases:
        for task in phase.tasks:
            total += 1
            if task.status == "done":
                done += 1
            elif task.status == "blocked":
                blocked += 1

    if total == 0:
        return "无任务"

    return (
        f"总计: {total} | 完成: {done} | 阻塞: {blocked} | "
        f"待处理: {total - done - blocked} | 进度: {done}/{total} ({done*100//total}%)"
    )
