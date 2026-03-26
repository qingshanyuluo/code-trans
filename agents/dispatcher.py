"""
Dispatcher Agent — LLM 驱动的智能文件定位

优先级:
  1. 使用 Planner 在计划中指定的目标文件 (target_files)
  2. 调用 LLM 根据任务描述 + 文件摘要智能匹配
  3. 兜底: 扫描项目全部源文件
"""

import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import LLM_MODEL
from utils.scanner import scan_project
from prompts.dispatcher_prompt import (
    DISPATCHER_SYSTEM_PROMPT,
    DISPATCHER_USER_PROMPT_TEMPLATE,
)


def create_dispatcher_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=0,
        max_retries=3,
        request_timeout=60,
    )


def resolve_target_files(project_path: str, relative_files: list[str]) -> list[str]:
    """将 Planner 指定的相对路径解析为绝对路径，跳过不存在的文件。"""
    resolved = []
    for rel_path in relative_files:
        abs_path = os.path.join(project_path, rel_path)
        if os.path.isfile(abs_path):
            resolved.append(abs_path)
    return resolved


def _build_file_summaries(project_path: str, all_files: list[str], max_lines: int = 15) -> str:
    """为每个文件生成内容摘要（前 N 行），供 LLM 判断文件相关性。"""
    summaries = []
    for filepath in all_files:
        rel_path = os.path.relpath(filepath, project_path)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                head = ''.join(f.readline() for _ in range(max_lines))
            summaries.append(f"### {rel_path}\n```\n{head.rstrip()}\n```")
        except (IOError, OSError):
            summaries.append(f"### {rel_path}\n```\n# [无法读取]\n```")
    return "\n\n".join(summaries)


def find_target_files_with_llm(task_description: str, project_path: str) -> list[str]:
    """
    使用 LLM 根据任务描述 + 文件摘要智能判断需要修改的文件。
    当 Planner 未指定目标文件时调用。
    """
    all_files = scan_project(project_path)
    if not all_files:
        return []

    file_summaries = _build_file_summaries(project_path, all_files)

    llm = create_dispatcher_llm()
    user_prompt = DISPATCHER_USER_PROMPT_TEMPLATE.format(
        task_description=task_description,
        file_summaries=file_summaries,
    )

    response = llm.invoke([
        SystemMessage(content=DISPATCHER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    result_files = []
    for line in response.content.strip().splitlines():
        line = line.strip().lstrip('- ')
        if not line:
            continue
        abs_path = os.path.join(project_path, line)
        if os.path.isfile(abs_path):
            result_files.append(abs_path)

    return result_files
