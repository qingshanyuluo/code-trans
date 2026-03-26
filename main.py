"""
代码迁移 Agent — CLI 入口

用法:
    python main.py --rule '把 Python 2 代码转换为 Python 3' --input-dir ./test_project --output-dir ./output
"""

import argparse
import os
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(
        description="代码迁移 Agent — 基于 LangGraph 的多 Agent 代码迁移流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py \\
      --rule '把 Python 2 代码转换为 Python 3' \\
      --input-dir ./test_project \\
      --output-dir ./output

  python main.py \\
      --rule '将 Django 3.x 项目升级到 Django 4.2，处理所有 deprecation' \\
      --input-dir ./my_django_app \\
      --output-dir ./my_django_app_v4

环境变量 (.env):
  OPENAI_API_KEY       API Key (必需)
  OPENAI_API_BASE      API Base URL
  LLM_MODEL            模型名称 (默认: gpt-4o-mini)
  LLM_TEMPERATURE      温度 (默认: 0)
  MAX_RETRY_COUNT      Fixer 最大重试次数 (默认: 3)
  PYTHON_EXECUTABLE    Python 解释器路径 (默认: python3)
  USE_RUFF_LINTER      是否使用 ruff lint (默认: false)
        """,
    )

    parser.add_argument(
        "--rule", "-r",
        required=True,
        help="迁移规则，自然语言描述 (如: '把 Python 2 代码转换为 Python 3')",
    )
    parser.add_argument(
        "--input-dir", "-i",
        required=True,
        help="源项目目录 (只读，不会被修改)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        required=True,
        help="输出目录 (迁移结果写入此处)",
    )

    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)

    if not os.path.isdir(input_dir):
        print(f"❌ 输入目录不存在: {input_dir}")
        sys.exit(1)

    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your-api-key-here":
        print("❌ 请在 .env 文件中设置有效的 OPENAI_API_KEY")
        sys.exit(1)

    # 将 input-dir 拷贝到 output-dir（保留原始项目不动）
    if os.path.exists(output_dir):
        print(f"⚠️  输出目录已存在，将清空: {output_dir}")
        shutil.rmtree(output_dir)

    shutil.copytree(input_dir, output_dir)
    print(f"📁 已将源项目复制到输出目录: {output_dir}")

    from graph import run_migration
    run_migration(
        project_path=output_dir,
        rule=args.rule,
    )


if __name__ == "__main__":
    main()
