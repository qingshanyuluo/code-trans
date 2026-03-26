"""
Planner Agent — 扫描项目并生成 MIGRATION_PLAN.md
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import LLM_MODEL, LLM_TEMPERATURE, MIGRATION_PLAN_FILENAME
from utils.scanner import get_project_summary
from prompts.planner_prompt import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT_TEMPLATE


def create_planner_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_retries=5,
        request_timeout=120,
    )


def run_planner(state: dict) -> dict:
    project_path = state["project_path"]
    rule = state.get("rule", "")

    print("\n" + "=" * 60)
    print("🔍 [Planner] 正在扫描项目...")
    print(f"   迁移规则: {rule}")
    print("=" * 60)

    project_summary = get_project_summary(project_path)
    print(f"📊 项目概要已生成 (项目路径: {project_path})")

    llm = create_planner_llm()
    user_prompt = PLANNER_USER_PROMPT_TEMPLATE.format(
        rule=rule,
        project_summary=project_summary,
    )

    print("🤖 [Planner] 正在生成迁移计划...")
    response = llm.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    plan_content = response.content.strip()

    # 3. 写入 MIGRATION_PLAN.md
    plan_path = os.path.join(project_path, MIGRATION_PLAN_FILENAME)
    with open(plan_path, 'w', encoding='utf-8') as f:
        f.write(plan_content)

    print(f"📝 迁移计划已写入: {plan_path}")
    print("─" * 40)
    print(plan_content[:500] + ("..." if len(plan_content) > 500 else ""))
    print("─" * 40)

    return {
        "plan_generated": True,
        "plan_path": plan_path,
    }
