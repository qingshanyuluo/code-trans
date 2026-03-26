"""
LangGraph 主图编排 — 顺序流水线: Planner → Dispatcher → Worker → Validator → Collector 闭环

流程:
  START → planner → dispatcher → worker → validator → [fixer|collector]
  fixer → validator (重试循环)
  collector → dispatcher (循环处理下一个文件/任务) 或 END
"""

import os
from typing import TypedDict, Optional, List

from langgraph.graph import StateGraph, START, END

from config import MAX_RETRY_COUNT
from agents.planner import run_planner
from agents.worker import run_worker
from agents.fixer import run_fixer
from utils.validator import validate_file
from utils.plan_parser import (
    update_task_status,
    get_next_pending_task,
    get_progress_summary,
)
from utils.scanner import scan_project
from agents.dispatcher import resolve_target_files, find_target_files_with_llm


# ============================================================
# 1. State 定义
# ============================================================

class PipelineState(TypedDict):
    project_path: str
    rule: str
    plan_path: str
    plan_generated: bool
    current_task_id: str
    current_task_description: str
    pending_files: List[str]
    file_path: str
    worker_result: Optional[dict]
    validation_error: str
    retry_count: int
    completed: bool


# ============================================================
# 2. 节点函数
# ============================================================

def planner_node(state: PipelineState) -> dict:
    result = run_planner(state)
    return result


def dispatcher_node(state: PipelineState) -> dict:
    """
    Dispatcher: 从文件队列中取下一个文件，或加载下一个任务。
    顺序处理，每次只发一个文件给 Worker。
    """
    plan_path = state["plan_path"]
    project_path = state["project_path"]
    pending_files = state.get("pending_files", [])
    current_task_id = state.get("current_task_id", "")

    # 如果上一个任务还有 pending_files，继续处理
    if pending_files:
        next_file = pending_files[0]
        remaining = pending_files[1:]
        print(f"\n📂 [Dispatcher] 继续任务 {current_task_id}，处理文件: {next_file}")
        print(f"   剩余文件数: {len(remaining)}")
        return {
            "file_path": next_file,
            "pending_files": remaining,
            "worker_result": None,
            "validation_error": "",
            "retry_count": 0,
        }

    # 如果当前任务有 ID，说明上一个任务的文件已全部处理完毕，标记完成
    if current_task_id and current_task_id != "__INIT__":
        update_task_status(plan_path, current_task_id, "done")
        print(f"\n✅ [Dispatcher] 任务 {current_task_id} 已完成")
        print(f"📊 {get_progress_summary(plan_path)}")

    # 获取下一个待处理的任务
    task = get_next_pending_task(plan_path)

    if task is None:
        print(f"\n🎉 [Dispatcher] 所有任务已完成!")
        print(f"📊 {get_progress_summary(plan_path)}")
        return {
            "current_task_id": "__DONE__",
            "current_task_description": "",
            "file_path": "",
            "pending_files": [],
            "completed": True,
        }

    print(f"\n📋 [Dispatcher] 新任务: {task.id} — {task.description}")
    update_task_status(plan_path, task.id, "in_progress")

    # 三级文件定位策略
    matching_files = []

    # 1) Planner 指定的目标文件（优先级最高）
    if task.target_files:
        matching_files = resolve_target_files(project_path, task.target_files)
        if matching_files:
            print(f"📂 [Dispatcher] 使用 Planner 指定的目标文件:")
        else:
            print(f"⚠️  [Dispatcher] Planner 指定的文件不存在: {task.target_files}")

    # 2) LLM 智能匹配（Planner 未指定或文件不存在时）
    if not matching_files:
        print(f"🤖 [Dispatcher] 调用 LLM 智能匹配目标文件...")
        matching_files = find_target_files_with_llm(task.description, project_path)

    # 3) 兜底: 扫描全部源文件
    if not matching_files:
        print("⚠️  [Dispatcher] LLM 未匹配到文件，扫描所有源文件")
        matching_files = scan_project(project_path)

    print(f"📂 [Dispatcher] 找到 {len(matching_files)} 个相关文件:")
    for f in matching_files:
        print(f"   - {f}")

    if not matching_files:
        return {
            "current_task_id": task.id,
            "current_task_description": task.description,
            "file_path": "",
            "pending_files": [],
            "worker_result": None,
            "validation_error": "",
            "retry_count": 0,
        }

    first_file = matching_files[0]
    remaining = matching_files[1:]

    return {
        "current_task_id": task.id,
        "current_task_description": task.description,
        "file_path": first_file,
        "pending_files": remaining,
        "worker_result": None,
        "validation_error": "",
        "retry_count": 0,
    }


def worker_node(state: PipelineState) -> dict:
    if state.get("current_task_id") == "__DONE__" or not state.get("file_path"):
        return state
    return run_worker(state)


def validator_node(state: PipelineState) -> dict:
    file_path = state.get("file_path", "")
    worker_result = state.get("worker_result")
    task_id = state.get("current_task_id", "")

    if task_id == "__DONE__" or not file_path:
        return state

    if not worker_result or not worker_result.get("success", False):
        return {
            "validation_error": worker_result.get("error", "Worker 执行失败") if worker_result else "无 Worker 结果",
        }

    print(f"\n🔍 [Validator] 正在验证: {file_path}")
    result = validate_file(file_path)

    if result["success"]:
        print(f"✅ [Validator] 验证通过: {file_path}")
        return {"validation_error": ""}
    else:
        error_msg = ""
        if not result["compile_ok"]:
            error_msg += f"编译错误: {result['compile_error']}\n"
        if not result["lint_ok"]:
            error_msg += f"Lint 错误: {result['lint_error']}\n"
        print(f"❌ [Validator] 验证失败: {file_path}")
        print(f"   {error_msg.strip()}")
        return {"validation_error": error_msg.strip()}


def fixer_node(state: PipelineState) -> dict:
    return run_fixer(state)


def collector_node(state: PipelineState) -> dict:
    """聚合单个文件的处理结果，决定下一步。"""
    task_id = state.get("current_task_id", "")
    file_path = state.get("file_path", "")
    validation_error = state.get("validation_error", "")
    retry_count = state.get("retry_count", 0)

    if task_id == "__DONE__":
        return state

    if not validation_error:
        print(f"📌 [Collector] 任务 {task_id} 文件 {file_path} — 成功")
    elif retry_count >= MAX_RETRY_COUNT:
        print(f"🚫 [Collector] 任务 {task_id} 文件 {file_path} — 标记 Blocked (重试 {retry_count} 次)")
    else:
        print(f"⚠️  [Collector] 任务 {task_id} 文件 {file_path} — 有错误但已处理")

    return state


# ============================================================
# 3. 路由函数
# ============================================================

def after_dispatcher_route(state: PipelineState) -> str:
    if state.get("current_task_id") == "__DONE__":
        return END
    if not state.get("file_path"):
        return "dispatcher"
    return "worker"


def after_validator_route(state: PipelineState) -> str:
    task_id = state.get("current_task_id", "")
    if task_id == "__DONE__":
        return "collector"

    validation_error = state.get("validation_error", "")
    retry_count = state.get("retry_count", 0)

    if not validation_error:
        return "collector"
    elif retry_count < MAX_RETRY_COUNT:
        return "fixer"
    else:
        return "collector"


def after_collector_route(state: PipelineState) -> str:
    if state.get("completed") or state.get("current_task_id") == "__DONE__":
        return END
    return "dispatcher"


# ============================================================
# 4. 构建图
# ============================================================

def build_migration_graph():
    """
    顺序流水线:
      START → planner → dispatcher → worker → validator → [fixer|collector]
      fixer → validator (重试)
      collector → dispatcher (下一个文件/任务) | END
    """
    graph = StateGraph(PipelineState)

    graph.add_node("planner", planner_node)
    graph.add_node("dispatcher", dispatcher_node)
    graph.add_node("worker", worker_node)
    graph.add_node("validator", validator_node)
    graph.add_node("fixer", fixer_node)
    graph.add_node("collector", collector_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "dispatcher")

    graph.add_conditional_edges("dispatcher", after_dispatcher_route, {
        "worker": "worker",
        "dispatcher": "dispatcher",
        END: END,
    })

    graph.add_edge("worker", "validator")

    graph.add_conditional_edges("validator", after_validator_route, {
        "collector": "collector",
        "fixer": "fixer",
    })

    graph.add_edge("fixer", "validator")

    graph.add_conditional_edges("collector", after_collector_route, {
        "dispatcher": "dispatcher",
        END: END,
    })

    return graph.compile()


def run_migration(project_path: str, rule: str):
    graph = build_migration_graph()

    initial_state: PipelineState = {
        "project_path": os.path.abspath(project_path),
        "rule": rule,
        "plan_path": os.path.join(os.path.abspath(project_path), "MIGRATION_PLAN.md"),
        "plan_generated": False,
        "current_task_id": "__INIT__",
        "current_task_description": "",
        "pending_files": [],
        "file_path": "",
        "worker_result": None,
        "validation_error": "",
        "retry_count": 0,
        "completed": False,
    }

    print("🚀 代码迁移 Agent 启动")
    print(f"   项目路径: {project_path}")
    print(f"   迁移规则: {rule}")
    print("=" * 60)

    for event in graph.stream(initial_state, {"recursion_limit": 200}):
        for node_name, _ in event.items():
            if node_name not in ("__start__",):
                pass

    print("\n" + "=" * 60)
    plan_path = os.path.join(os.path.abspath(project_path), "MIGRATION_PLAN.md")
    if os.path.exists(plan_path):
        print(f"📊 最终进度: {get_progress_summary(plan_path)}")
    print("🏁 迁移流水线执行完毕")
