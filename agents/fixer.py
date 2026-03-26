"""
Fixer Agent — 根据错误日志修复代码，支持重试机制
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import LLM_MODEL, LLM_TEMPERATURE
from utils.file_ops import read_file, write_file
from prompts.fixer_prompt import FIXER_SYSTEM_PROMPT, FIXER_USER_PROMPT_TEMPLATE


def create_fixer_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=0.2,
        max_retries=5,
        request_timeout=120,
    )


def run_fixer(state: dict) -> dict:
    """
    Fixer Agent 节点函数。

    接收原代码、修改后代码、错误日志，调用 LLM 修复代码。

    输入 State 字段:
      - file_path: 文件路径
      - worker_result: 包含 original_content, modified_content
      - validation_error: 验证错误信息
      - retry_count: 当前重试次数

    输出 State 更新:
      - worker_result: 更新为修复后的结果
      - retry_count: +1
    """
    file_path = state["file_path"]
    worker_result = state.get("worker_result", {})
    validation_error = state.get("validation_error", "")
    retry_count = state.get("retry_count", 0)

    original_content = worker_result.get("original_content", "")
    modified_content = worker_result.get("modified_content", "")

    print(f"\n🔧 [Fixer] 正在修复: {file_path} (重试 #{retry_count + 1})")
    print(f"   错误: {validation_error[:200]}...")

    # 构造 Prompt 并调用 LLM
    llm = create_fixer_llm()
    user_prompt = FIXER_USER_PROMPT_TEMPLATE.format(
        file_path=file_path,
        original_content=original_content,
        modified_content=modified_content,
        error_log=validation_error,
    )

    response = llm.invoke([
        SystemMessage(content=FIXER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    fixed_content = response.content.strip()

    # 去除可能的代码块标记
    if fixed_content.startswith("```python"):
        fixed_content = fixed_content[len("```python"):].strip()
    if fixed_content.startswith("```"):
        fixed_content = fixed_content[3:].strip()
    if fixed_content.endswith("```"):
        fixed_content = fixed_content[:-3].strip()

    # 写入修复后的代码
    write_file(file_path, fixed_content + "\n", backup=False)
    print(f"✅ [Fixer] 已修复: {file_path}")

    # 更新 worker_result
    updated_result = {
        **worker_result,
        "modified_content": fixed_content,
    }

    return {
        **state,
        "worker_result": updated_result,
        "retry_count": retry_count + 1,
    }
