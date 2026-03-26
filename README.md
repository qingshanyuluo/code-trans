# Code Migration Agent

基于 LangGraph 的多 Agent 代码迁移流水线。通过自然语言描述迁移规则，自动完成代码库的批量转换。

---

## 一、系统架构

### 核心理念：状态外置，任务降维，环境隔离

系统不依赖一个拥有"无限记忆"的超级 Agent，而是建立一条**流水线**：

- **状态外置** — 状态机由物理文件 `MIGRATION_PLAN.md` 维护，而非 LLM 对话历史
- **任务降维** — 宏观迁移规则被逐层拆解为「单文件 × 单转换模式」的原子操作
- **环境隔离** — 每个 Worker 无状态启动，杜绝上下文污染；输出目录与源目录隔离

### 角色定义

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   START ──▶ Planner ──▶ Dispatcher ──▶ Worker ──▶ Validator         │
│                            ▲              │           │             │
│                            │              │      ┌────┴────┐        │
│                            │              │      │  Fixer  │        │
│                            │              │      └────┬────┘        │
│                            │              │           │             │
│                            │         Collector ◀──────┘             │
│                            │              │                         │
│                            └──────────────┘                         │
│                          (下一个文件/任务)                           │
│                                                                     │
│                          到达终点 ──▶ END                            │
└─────────────────────────────────────────────────────────────────────┘
```

| 角色 | 职责 | 特点 |
|------|------|------|
| **Planner** | 扫描项目，根据迁移规则生成 `MIGRATION_PLAN.md` | 只运行一次，全局审视 |
| **Dispatcher** | 解析 Todo 列表，用 grep/正则定位文件，逐个分发给 Worker | 流程控制，不写代码 |
| **Worker** | 接收「单指令 + 单文件」，调用 LLM 重写代码 | **无状态**，每次全新启动 |
| **Fixer** | 接收「原代码 + 改后代码 + 报错日志」，修复编译错误 | 最多重试 3 次 |
| **Validator** | 执行 `py_compile` + 可选 `ruff` lint | 客观验证，不依赖 LLM |

### 执行闭环

```
1. Planner 生成计划（MIGRATION_PLAN.md）
2. Dispatcher 取下一个 pending 任务 → grep 定位文件 → 取第一个文件
3. Worker 修改该文件
4. Validator 编译检查
   ├── 通过 → Collector 标记成功 → 回到 Dispatcher（下一个文件）
   └── 失败 → Fixer 修复 → 重新验证（最多 3 次，超限标记 Blocked）
5. 当前任务所有文件处理完 → 标记 [x] → 取下一个任务
6. 所有任务完成 → END
```

### 防爆炸隔离机制

传统方案将整个项目喂给一个 Agent，导致上下文爆炸。本系统的解法：

1. **Planner 只看摘要** — 文件列表 + 每个文件的完整内容，不含修改历史
2. **Dispatcher 用脚本定位** — 正则 grep 而非 LLM 搜索，精准且零 token 消耗
3. **Worker 只看一个文件** — 每次调用只传入单个文件内容 + 单条指令
4. **Fixer 只看三样东西** — 原代码、改后代码、报错日志，不看项目全貌

---

## 二、项目结构

```
code-trans/
├── main.py                  # CLI 入口
├── graph.py                 # LangGraph 流水线编排
├── config.py                # 全局配置（从 .env 加载）
├── agents/
│   ├── planner.py           # Planner Agent
│   ├── dispatcher.py        # Dispatcher 搜索模式提取
│   ├── worker.py            # Worker Agent（无状态）
│   └── fixer.py             # Fixer Agent（错误修复）
├── prompts/
│   ├── planner_prompt.py    # Planner 系统提示词
│   ├── worker_prompt.py     # Worker 系统提示词
│   └── fixer_prompt.py      # Fixer 系统提示词
├── utils/
│   ├── scanner.py           # 项目扫描、grep 搜索
│   ├── validator.py         # 编译检查 + lint 检查
│   ├── plan_parser.py       # MIGRATION_PLAN.md 解析与状态更新
│   └── file_ops.py          # 文件读写（带 .bak 备份）
├── test_project/            # 示例 Python 2 项目（用于测试）
├── requirements.txt
├── .env.example             # 环境变量模板
└── README.md
```

---

## 三、快速启动

### 1. 环境准备

```bash
# 克隆项目
git clone <repo-url> && cd code-trans

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 LLM API 信息：

```env
# LLM API 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://your-llm-gateway.example.com/v1

# 模型配置
LLM_MODEL=OpenAI-GPT-5.1
LLM_TEMPERATURE=1.0
```

### 3. 运行迁移

```bash
python main.py \
    --rule '把 Python 2 代码转换为 Python 3' \
    --input-dir ./test_project \
    --output-dir ./output
```

参数说明：

| 参数 | 简写 | 必填 | 说明 |
|------|------|------|------|
| `--rule` | `-r` | 是 | 迁移规则（自然语言） |
| `--input-dir` | `-i` | 是 | 源项目目录（只读，不会被修改） |
| `--output-dir` | `-o` | 是 | 输出目录（迁移结果写入此处） |

---

## 四、运行示例

### Python 2 → Python 3

```bash
python main.py \
    --rule '把 Python 2 代码转换为 Python 3' \
    --input-dir ./test_project \
    --output-dir ./output
```

典型输出：

```
📁 已将源项目复制到输出目录: ./output
🚀 代码迁移 Agent 启动
   项目路径: ./output
   迁移规则: 把 Python 2 代码转换为 Python 3
============================================================
🔍 [Planner] 正在扫描项目...
🤖 [Planner] 正在生成迁移计划...
📝 迁移计划已写入: ./output/MIGRATION_PLAN.md

📋 [Dispatcher] 新任务: 1.1 — 将 print 语句迁移为 print() 函数
📂 [Dispatcher] 找到 3 个相关文件
🔧 [Worker] 正在处理: main.py
✅ [Validator] 验证通过: main.py
...
📊 最终进度: 总计: 13 | 完成: 13 | 阻塞: 0 | 进度: 13/13 (100%)
🏁 迁移流水线执行完毕
```

### 其他迁移场景（示例命令）

```bash
# Django 升级
python main.py \
    --rule '将 Django 3.x 升级到 Django 4.2，处理所有 deprecated API' \
    --input-dir ./my_django_app \
    --output-dir ./my_django_app_v4

# Flask 迁移
python main.py \
    --rule '将 Flask 1.x 迁移到 Flask 3.0，更新蓝图注册方式' \
    --input-dir ./flask_app \
    --output-dir ./flask_app_v3

# 代码风格统一
python main.py \
    --rule '将所有字符串格式化从 % 和 .format() 统一为 f-string' \
    --input-dir ./legacy_code \
    --output-dir ./modernized
```

---

## 五、配置参考

### .env 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | — | API Key（必填） |
| `OPENAI_API_BASE` | — | API Base URL |
| `LLM_MODEL` | `gpt-4o-mini` | 模型名称 |
| `LLM_TEMPERATURE` | `0` | 生成温度 |
| `MAX_RETRY_COUNT` | `3` | Fixer 最大重试次数 |
| `PYTHON_EXECUTABLE` | `python3` | 用于 `py_compile` 验证的解释器 |
| `USE_RUFF_LINTER` | `false` | 是否启用 ruff lint 检查 |

### MIGRATION_PLAN.md 状态标记

| 标记 | 含义 |
|------|------|
| `- [ ]` | 待处理 (pending) |
| `- [/]` | 进行中 (in_progress) |
| `- [x]` | 已完成 (done) |
| `- [Blocked]` | 阻塞（重试超限） |

迁移过程中可以随时查看 `<output-dir>/MIGRATION_PLAN.md` 了解进度。

---

## 六、技术栈

- **LangGraph** — 状态图编排，驱动 Agent 间的流转与循环
- **LangChain OpenAI** — LLM 调用层，兼容 OpenAI API 协议的任意后端
- **py_compile** — Python 内置编译检查，零依赖验证语法正确性
- **ruff** — 可选的高速 linter（通过 `USE_RUFF_LINTER=true` 启用）
