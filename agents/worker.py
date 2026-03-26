"""
Worker Agent — 无状态的代码修改执行者
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import LLM_MODEL, LLM_TEMPERATURE
from utils.file_ops import read_file, write_file
from prompts.worker_prompt import WORKER_SYSTEM_PROMPT, WORKER_USER_PROMPT_TEMPLATE


def create_worker_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_retries=5,
        request_timeout=120,
    )


def run_worker(state: dict) -> dict:
    """
    Worker Agent 节点函数（无状态）。

    接收单一指令 + 单一文件，调用 LLM 修改代码，写回文件。

    输入 State 字段:
      - file_path: 待修改的文件路径
      - current_task_description: 转换指令描述
      - current_task_id: 任务 ID

    输出 State 更新:
      - worker_result: 修改结果 dict
    """
    file_path = state["file_path"]
    task_description = state["current_task_description"]
    task_id = state["current_task_id"]

    # 处理 __DONE__ 哨兵值
    if task_id == "__DONE__":
        return state

    print(f"\n🔧 [Worker] 正在处理: {file_path}")
    print(f"   指令: {task_description}")

    # 1. 读取文件内容
    try:
        file_content = read_file(file_path)
    except FileNotFoundError:
        print(f"❌ [Worker] 文件不存在: {file_path}")
        return {
            **state,
            "worker_result": {
                "file_path": file_path,
                "task_id": task_id,
                "success": False,
                "error": f"文件不存在: {file_path}",
                "original_content": "",
                "modified_content": "",
            },
        }

    original_content = file_content

    # 2. 构造 Prompt 并调用 LLM
    llm = create_worker_llm()
    user_prompt = WORKER_USER_PROMPT_TEMPLATE.format(
        instruction=task_description,
        file_path=file_path,
        file_content=file_content,
    )

    response = llm.invoke([
        SystemMessage(content=WORKER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    modified_content = response.content.strip()

    # 去除可能被 LLM 包裹的代码块标记
    if modified_content.startswith("```python"):
        modified_content = modified_content[len("```python"):].strip()
    if modified_content.startswith("```"):
        modified_content = modified_content[3:].strip()
    if modified_content.endswith("```"):
        modified_content = modified_content[:-3].strip()

    # 3. 写入文件（带备份）
    write_file(file_path, modified_content + "\n")
    print(f"✅ [Worker] 已修改: {file_path}")

    return {
        **state,
        "worker_result": {
            "file_path": file_path,
            "task_id": task_id,
            "success": True,
            "error": "",
            "original_content": original_content,
            "modified_content": modified_content,
        },
    }
