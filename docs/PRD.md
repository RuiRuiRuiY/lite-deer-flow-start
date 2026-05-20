# Lite-DeerFlow — Product Requirements Document

> 轻量级 AI 研究 Agent，参考 DeerFlow 核心设计理念，基于 LangChain DeepAgents 从零构建。

---

## 1. 产品定位

**一句话**：个人开发者的轻量研究 Agent —— 支持深度搜索、多步研究、报告生成，单进程可运行、一个 `config.yaml` 可配置。

**目标用户**：个人开发者，本地 Windows 环境使用。

**核心价值**：

- 能搜索、能阅读、能写报告
- 跨会话记忆，越用越懂你
- 多模型容灾，主模型挂了自动切备用
- 本地运行，数据不出本机

---

## 2. DeerFlow 能力裁剪矩阵

### 2.1 保留（核心价值）

| 模块                   | 简化策略                                                                                 |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| **Lead Agent**   | 用 DeepAgents `create_deep_agent()` 替代自研                                           |
| **Sub-Agents**   | 固定 2 个：research-agent + report-agent，不做动态分工                                   |
| **Sandbox**      | 仅 FilesystemBackend（纯文件操作），无 shell 执行、无 Docker/K8s |
| **Memory**       | Phase 1: AGENTS.md 手动文件；Phase 3: LLM 自动提取（预留接口）                           |
| **Skills**       | DeepAgents 原生支持，内置 research + report 两个 skill                                   |
| **Tools**        | web_search(Tavily)、web_fetch、read_file、write_file、edit_file、bash(Git Bash)          |
| **多模型切换**   | 用户自主选择 + 自动 fallback（`with_fallbacks()`）                                     |
| **Context 管理** | DeepAgents 原生支持（offload + summarization 默认开启） |
| **Streaming**    | Phase 1 实现 SSE 流式输出（LangGraph `astream` 开箱即用）                              |
| **HITL 中断**    | DeepAgents 原生 `interrupt_on` 支持（需配合 `checkpointer`）                         |

### 2.2 裁剪（个人开发者不需要）

| 模块                      | 裁剪理由                                   |
| ------------------------- | ------------------------------------------ |
| Nginx 反向代理            | 单进程架构，FastAPI 直接暴露               |
| 独立 LangGraph Server     | 合并到 Gateway 进程内                      |
| Provisioner (K8s)         | 个人用户不用 K8s                           |
| IM Channels（6 个平台）   | Telegram/Slack/飞书/微信/企微/钉钉 — 全砍 |
| MCP Server 管理           | 配置复杂，内置工具够用                     |
| LangSmith/Langfuse 双追踪 | 保留 LangSmith 单追踪                      |
| Artifact 独立系统         | 产物类型单一（报告），直接文件读取即可     |
| 前端完整功能              | Phase 1 用 Streamlit，不写 Next.js         |
| Docker 部署               | 本地 Windows 环境，不需要                  |

---

## 3. 技术架构

### 3.1 整体架构

```
┌──────────────────────────────────────────┐
│         Lite-DeerFlow (单进程)            │
│                                          │
│  FastAPI (端口 8000)                      │
│  ├── POST /api/threads       创建会话     │
│  ├── GET  /api/threads/{id}  获取会话     │
│  ├── POST /api/runs          执行任务     │
│  ├── POST /api/runs/{id}/cancel 取消任务  │
│  ├── GET  /api/models        模型列表     │
│  ├── PUT  /api/models/active 切换模型     │
│  ├── GET  /api/memory        获取记忆     │
│  └── PUT  /api/memory        更新记忆     │
│                                          │
│  DeepAgents (LangGraph)                   │
│  ├── Lead Agent (协调者)                  │
│  │   ├── 工具：task, todos, 文件系统      │
│  │   ├── 上下文管理：offload + summarization（默认开启）│
  │   │   ├── 记忆：memory=["/AGENTS.md"]        │
│  │   ├── 模型：with_fallbacks([备用模型])  │
│  │   └── 安全：checkpointer + recursion_limit │
│  ├── research-agent (研究专家)            │
│  │   ├── 工具：web_search, web_fetch,     │
│  │   │        read_file, write_file       │
│  │   ├── skills: ["./skills/research/"]   │
│  │   └── 职责：搜索、提取、写入工作文件    │
│  └── report-agent (写作专家)              │
│      ├── 工具：read_file, write_file,     │
│      │        edit_file                   │
│      ├── skills: ["./skills/report/"]     │
│      └── 职责：基于研究结果撰写报告        │
│                                          │
│  Local Sandbox (文件系统)                      │
│  ├── FilesystemBackend(root_dir, virtual_mode=True) │
│  └── 文件操作：ls, read_file, write_file, edit_file, glob, grep │
│                                          │
│  Memory 系统                             │
│  ├── Phase 1: AGENTS.md 手动文件          │
│  │   └── memory=["/AGENTS.md"] 自动注入     │
│  ├── Phase 3: LLM 自动提取事实/偏好       │
│  └── 跨线程记忆：Store + CompositeBackend  │
│                                          │
│  持久化层                                │
│  ├── Checkpointer: AsyncSqliteSaver       │
│  └── Store: InMemoryStore / JsonStore     │
│                                          │
│  Web Search                              │
│  ├── 主: Tavily (1000次/月免费)           │
│  └── 备用: SerpApi (免费)              │
└──────────────────────────────────────────┘
         │
    ┌────┴─────┐
    │ Streamlit │  聊天界面 + 模型选择 + 记忆查看
    │  前端     │  文件预览 + 报告下载
    └──────────┘
```

### 3.2 技术栈

| 层级             | 选型                                  | 理由                                    |
| ---------------- | ------------------------------------- | --------------------------------------- |
| 包管理           | uv                                    | 替代 pip/venv，快 10-100x，依赖锁定     |
| Agent 框架       | LangGraph + DeepAgents                | 官方 harness，覆盖 70% 能力             |
| LLM 适配         | LangChain + langchain-openai          | 统一 OpenAI 兼容接口，支持 base_url 覆盖 |
| 后端 API         | FastAPI + uvicorn                     | 轻量、异步、类型安全                    |
| 前端             | Streamlit                             | 快速验证，无需前端工程化                |
| 搜索工具         | Tavily（langchain-tavily `TavilySearch` 新版 API）+ SerpApi | 免费额度 + fallback      |
| 配置格式         | YAML (config.yaml)                    | 与 DeerFlow 一致                        |
| 记忆存储         | JSON 文件 / Markdown                  | 简单、可读、可手动编辑                  |
| Checkpointer     | AsyncSqliteSaver（langgraph-checkpoint-sqlite） | 轻量、跨会话持久化、支持 HITL |
| Store            | InMemoryStore (Phase 1)               | 跨线程记忆，Phase 3 可换持久化          |
| 可观测性         | LangSmith（可选）                     | 免费额度，完整 trace                    |
| 代码质量         | ruff（lint + format）+ mypy（类型检查） | 零配置、快、统一风格                    |
| 测试             | pytest + pytest-asyncio               | Python 生态标准                          |

### 3.3 项目结构 (Monorepo)

```
lite-deer-flow/
├── README.md
├── PRD.md                 # 本文档
├── config.example.yaml    # 配置模板
├── .env.example           # 环境变量模板
├── AGENTS.md              # 用户偏好文件（记忆）
│
├── backend/
│   ├── pyproject.toml     # 依赖 + ruff/mypy/pytest 配置
│   ├── .python-version    # uv 锁定 Python 版本
│   ├── uv.lock            # uv 锁定依赖版本
│   ├── .gitignore         # .venv/ .mypy_cache/ .ruff_cache/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI 入口
│   │   ├── agent/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI 入口
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── lead.py            # create_deep_agent() 工厂
│   │   │   │                      # + with_fallbacks() + checkpointer
│   │   │   ├── subagents.py       # research + report agent 定义
│   │   │   └── memory.py          # LLM 自动提取（Phase 3）
│   │   ├── gateway/
│   │   │   ├── __init__.py
│   │   │   ├── app.py             # FastAPI 应用组装
│   │   │   └── routers/
│   │   │       ├── __init__.py
│   │   │       ├── threads.py     # 会话管理
│   │   │       ├── runs.py        # 任务执行 + SSE 流式
│   │   │       ├── models.py      # 模型管理
│   │   │       └── memory.py      # 记忆管理
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   └── web_search.py      # Tavily + SerpApi
│   │   └── skills/
│   │       ├── research/
│   │       │   └── SKILL.md       # 研究技能
│   │       └── report/
│   │           └── SKILL.md       # 报告生成技能
│   └── tests/
│
├── frontend/
│   ├── requirements.txt
│   └── app.py                     # Streamlit 聊天界面
│
└── data/                          # 运行时数据（gitignore）
    ├── threads/                   # 会话工作文件
    ├── checkpoints.db             # SQLite checkpointer
    ├── memories/                  # 跨线程记忆（Phase 3）
    └── logs/                      # 执行日志
```

---

## 4. 核心功能设计

### 4.1 多模型动态切换

**设计原则**：用户自主选择 + 自动 fallback 两层机制。

```yaml
# config.yaml
models:
  primary:
    name: "deepseek-v4-pro"
    provider: "openai"
    model: "deepseek-v4-pro"
    base_url: "https://api.deepseek.com"
    api_key_env: "DEEPSEEK_API_KEY"

  fallback:
    name: "deepseek-v4-flash"
    provider: "openai"
    model: "deepseek-v4-flash"
    base_url: "https://api.deepseek.com"
    api_key_env: "DEEPSEEK_API_KEY"
```

**两层机制**：

| 层级                    | 功能                   | 触发方式     |
| ----------------------- | ---------------------- | ------------ |
| **用户自主选择**  | 前端/ API 切换活跃模型 | 用户主动操作 |
| **自动 Fallback** | 活跃模型失败时切备用   | 透明容灾     |

**Fallback 触发条件**：

- API 返回 429 (Rate Limit)
- API 返回 5xx (Server Error)
- 连接超时 (>30s)
- 认证失败 (401)

**技术实现**：使用 LangChain `with_fallbacks()` 包装模型：

```python
from langchain_openai import ChatOpenAI

# 根据用户选择确定活跃模型
active_model = ChatOpenAI(
    model=config["models"]["active"]["model"],
    base_url=config["models"]["active"]["base_url"],
    api_key=os.getenv(config["models"]["active"]["api_key_env"]),
)

# 备用模型
fallback_model = ChatOpenAI(
    model=config["models"]["fallback"]["model"],
    base_url=config["models"]["fallback"]["base_url"],
    api_key=os.getenv(config["models"]["fallback"]["api_key_env"]),
)

# 包装为带 fallback 的模型
model_with_fallback = active_model.with_fallbacks([fallback_model])

agent = create_deep_agent(model=model_with_fallback, ...)
```

**API 设计**：

```
GET  /api/models              # 返回所有可用模型和当前活跃模型
PUT  /api/models/active       # 手动切换活跃模型 {"active": "fallback"}
```

**前端**：Streamlit 侧边栏增加模型选择器（下拉框），切换后持久化到配置。

### 4.2 Sub-Agent 分工

**固定两个 Sub-Agent，不做动态分工**：

```python
subagents = [
    {
        "name": "research-agent",
        "description": "搜索互联网、提取网页内容、整理信息并写入工作文件",
        "system_prompt": "你是一个研究专家...",
        "tools": [web_search, web_fetch, read_file, write_file],
    },
    {
        "name": "report-agent",
        "description": "阅读研究文件，撰写结构化报告",
        "system_prompt": "你是一个专业的报告撰写人...",
        "tools": [read_file, write_file, edit_file],
    },
]
```

**分工流程**：

```
用户: "帮我研究 Rust 异步编程的最佳实践"

Lead Agent:
  1. 调用 task() → research-agent
      → 搜索 "Rust async best practices"
      → 提取 5 篇博客内容
      → 写入 workspace/research_notes.md
      → 返回摘要

  2. 调用 task() → report-agent
      → 读取 research_notes.md
      → 撰写结构化报告
      → 写入 workspace/report.md
      → 返回报告内容

  3. 向用户展示报告
```

**注意事项**：

- `task()` 是 DeepAgents 内置工具，Lead Agent 在对话中自然使用，无需手动编写委派逻辑
- 自定义 Sub-Agent（research-agent / report-agent）的 skills **不会从 Lead Agent 继承**，必须在创建时显式传入 `skills` 参数
- Sub-Agent 输出应保持简洁（摘要而非原始数据），避免主 Agent context 膨胀

**并发策略**：研究场景下两个 agent 通常串行（先研究再写报告），不需要并行控制。

### 4.3 Memory 系统

**Phase 1: AGENTS.md 手动文件**

```markdown
# AGENTS.md

## 用户偏好
- 主要编程语言: Python
- 数据库偏好: PostgreSQL
- 代码风格: 使用 type hints，遵循 PEP 8
- 报告语言: 中文

## 项目上下文
- 当前研究方向: AI Agent 架构
- 常用技术栈: FastAPI, LangChain, React
```

DeepAgents 原生支持：创建 agent 时传入 `memory=["/AGENTS.md"]`（POSIX 路径格式，带前导斜杠），每次启动自动读取并注入 system prompt。

**Phase 3: 跨线程记忆（CompositeBackend + Store）**

使用 `CompositeBackend` 将 `/memories/` 路径路由到 LangGraph Store，实现跨会话持久化：

```python
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

def make_backend(runtime):
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={"/memories/": StoreBackend(runtime)},
    )

agent = create_deep_agent(
    model=model_with_fallback,
    store=InMemoryStore(),
    backend=make_backend,
    memory=["/AGENTS.md"],
    system_prompt="用户偏好自动保存到 /memories/user_preferences.md",
)
```

**Phase 3: LLM 自动提取（预留接口）**

```python
# 对话结束后调用
async def extract_memory(conversation: list[Message]) -> MemoryEntry:
    """
    使用 LLM 分析对话，提取:
    - 用户偏好 (preferences)
    - 事实 (facts)
    - 项目上下文 (context)
    """
    # 写入 /memories/ 目录
    # 下次对话时通过 memory 参数自动注入
```

**记忆注入时机**：

- Phase 1: 用户手动编辑 AGENTS.md，通过 `memory=["/AGENTS.md"]` 自动加载
- Phase 3: 每次 run 结束后自动分析并写入 `/memories/`（可配置开关）

### 4.4 Web Search 工具

**主工具: Tavily**

- 1000 次/月免费
- 专为 Agent 优化，返回结构化摘要
- 支持深度搜索模式

**备用工具: SerpApi**

- 完全免费
- 不稳定，可能被限流
- 仅在 Tavily 不可用时触发

```python
async def web_search(query: str, max_results: int = 5) -> str:
    """搜索互联网并返回摘要结果"""
    try:
        return await tavily_search(query, max_results)
    except (APIError, RateLimitError):
        return await serp_search(query, max_results)
```

### 4.5 Sandbox / 文件系统

**FilesystemBackend 配置**（Windows 环境）：

```python
from deepagents.backends import FilesystemBackend

backend = FilesystemBackend(
    root_dir=f"data/threads/{thread_id}/",  # 每个线程独立目录
    virtual_mode=True,  # 限制路径访问，禁止 ../ 和 ~/ 逃逸
)
```

**文件操作工具**（DeepAgents 原生提供）：

- `ls` — 列出目录
- `read_file` — 读取文件（支持大文件 offset/limit）
- `write_file` — 创建文件
- `edit_file` — 精确字符串替换
- `glob` — 文件名模式匹配
- `grep` — 文件内容搜索

### 4.6 Skills 系统

**遵循 AgentSkills.io 标准**，DeepAgents 原生支持渐进式加载。

**内置 Skills**：

`backend/app/skills/research/SKILL.md`:

```markdown
---
name: research
description: 深度互联网研究技能
---

# Research Skill

你是一个研究专家。当需要深入调查一个主题时使用此技能。

## 工作流程
1. 将复杂问题分解为子问题
2. 对每个子问题进行针对性搜索
3. 提取关键信息并去重
4. 整理为结构化的研究笔记

## 最佳实践
- 使用具体的搜索关键词
- 交叉验证多个来源
- 记录信息来源 URL
- 区分事实和观点
```

`backend/app/skills/report/SKILL.md`:

```markdown
---
name: report
description: 撰写结构化报告
---

# Report Generation Skill

当需要基于研究结果撰写报告时使用此技能。

## 报告结构
1. 执行摘要
2. 背景介绍
3. 主要发现
4. 详细分析
5. 结论与建议
6. 参考资料

## 格式要求
- 使用 Markdown 格式
- 标题层级不超过 4 级
- 关键数据加粗
- 引用来源使用脚注
```

### 4.7 HITL 任务中断

**DeepAgents 原生支持** `interrupt_on` 参数（**必须配合 `checkpointer`**）：

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("data/checkpoints.db") as checkpointer:
    agent = create_deep_agent(
        model=model_with_fallback,
        checkpointer=checkpointer,
        interrupt_on={
            "write_file": True,      # 写文件前暂停确认
            "execute": True,         # 执行命令前暂停确认
        },
    )
```

**两种中断场景**：

| 场景                     | 实现                                           |
| ------------------------ | ---------------------------------------------- |
| 用户主动取消运行中的任务 | Gateway 层 cancel LangGraph run（不需要 HITL） |
| Agent 请求用户确认操作   | DeepAgents `interrupt_on` + `checkpointer` |

**API 设计**：

```
POST /api/threads/{id}/runs/{run_id}/cancel    # 取消正在执行的任务
POST /api/threads/{id}/runs/{run_id}/resume    # 恢复被中断的任务 {"approved": true, "message": "..."}
```

### 4.8 产物交付

**简化方案**（不照搬 DeerFlow 的 artifact 系统）：

1. Agent 将报告写入 `workspace/report.md`
2. Streamlit 前端读取并渲染 Markdown
3. 提供"下载报告"按钮（读取文件内容 → 触发浏览器下载）

**不需要**：

- 独立的 `/api/artifacts/` 端点
- 产物预览组件
- 多格式支持（PPTX/HTML/视频）

---

## 5. API 设计

### 5.1 会话管理

```
POST /api/threads
  Body: {"title": "Rust 异步编程研究"}
  Response: {"id": "thread_001", "title": "...", "created_at": "..."}

GET /api/threads
  Response: [{"id": "...", "title": "...", "updated_at": "..."}]

GET /api/threads/{id}
  Response: {"id": "...", "title": "...", "messages": [...]}

DELETE /api/threads/{id}
  Response: {"status": "deleted"}
```

### 5.2 任务执行

```
POST /api/threads/{id}/runs
  Body: {"content": "帮我研究 Rust 异步编程的最佳实践"}
  Response (同步): {
    "id": "run_001",
    "status": "completed",
    "result": "...",
    "artifacts": ["workspace/report.md"]
  }

GET /api/threads/{id}/runs/stream    # SSE 流式输出
  Body: {"content": "..."}
  Response: text/event-stream
    event: message
    data: {"type": "token", "content": "..."}
    event: complete
    data: {"result": "...", "artifacts": [...]}

POST /api/threads/{id}/runs/{run_id}/cancel
  Response: {"status": "cancelled"}

POST /api/threads/{id}/runs/{run_id}/resume
  Body: {"approved": true, "message": "继续"}
  Response: {"status": "resumed", "result": "..."}
```

**流式输出实现**（Phase 1 即支持）：

```python
from fastapi.responses import StreamingResponse

@router.get("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, content: str):
    config = {"configurable": {"thread_id": thread_id, "recursion_limit": 50}}
  
    async def event_stream():
        async for event in agent.astream(
            {"messages": [HumanMessage(content=content)]},
            config=config,
            stream_mode="messages",
        ):
            yield format_sse(event)
  
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 5.3 模型管理

```
GET /api/models
  Response: {
    "primary": {"name": "deepseek-v4-pro", "status": "available"},
    "fallback": {"name": "deepseek-v4-flash", "status": "available"},
    "active": "primary"
  }

PUT /api/models/active
  Body: {"active": "fallback"}
  Response: {"active": "fallback"}
```

### 5.4 记忆管理

```
GET /api/memory
  Response: {"content": "# 用户偏好\n- 语言: Python\n..."}

PUT /api/memory
  Body: {"content": "# 更新后的偏好\n..."}
  Response: {"status": "updated"}
```

---

## 6. 配置系统

### 6.1 config.yaml

```yaml
# Lite-DeerFlow 配置

models:
  primary:
    name: "deepseek-v4-pro
    provider: "openai"
    model: "deepseek-v4-pro"
    base_url: "https://api.deepseek.com/v1"
    api_key_env: "DEEPSEEK_API_KEY"

  fallback:
    name: "deepseek-v4-flash"
    provider: "openai"
    model: "deepseek-v4-flash"
    base_url: "https://api.openai.com/v1"
    api_key_env: "DEEPSEEK_API_KEY"

search:
  primary: tavily
  tavily_api_key_env: "TAVILY_API_KEY"
  fallback: serp_search

server:
  host: "127.0.0.1"
  port: 8000

sandbox:
  type: filesystem  # FilesystemBackend（纯文件操作）
  virtual_mode: true  # 限制路径访问

memory:
  type: agents_md  # Phase 1
  file: "AGENTS.md"
  # auto_extract: true  # Phase 3

skills:
  paths:
    - "backend/app/skills"

persistence:
  checkpointer: "sqlite"  # AsyncSqliteSaver
  db_path: "data/checkpoints.db"
  store: "memory"  # InMemoryStore (Phase 1), 可换持久化 (Phase 3)

agent:
  recursion_limit: 50  # 防止无限循环
  # summarization 默认已开启（DeepAgents 内置），无需额外配置
  # 如需手动压缩工具（compact_conversation），添加 create_summarization_tool_middleware 到 middleware 列表

observability:
  langsmith:
    enabled: false
    # endpoint: "https://api.smith.langchain.com"
    # api_key_env: "LANGSMITH_API_KEY"
    # project: "lite-deer-flow"
```

### 6.2 backend/pyproject.toml（开发工具配置）

运行时依赖 + 开发工具链（uv/ruff/mypy/pytest）统一配置在 `backend/pyproject.toml` 中：

- **uv 管理**依赖和虚拟环境（`uv sync` 替代 `pip install`）
- **ruff** 做 lint + format（`ruff check .`、`ruff format .`）
- **mypy** 做类型检查（渐进式：Phase 1 基础模式 → Phase 3 `strict`）
- **pytest** + `asyncio_mode = auto` 做测试

具体版本约束参考 [demo/pyproject.toml](./demo/pyproject.toml)。

### 6.3 .env

```env
# LLM API Keys
DEEPSEEK_API_KEY=sk-...

# Search
TAVILY_API_KEY=tvly-...

# Observability (optional)
LANGSMITH_API_KEY=lsv2_...
```

---

## 7. 分阶段路线图

### Phase 0: Agent 核心验证（1-2 天）

**目标**：在已有的项目骨架中实现 Agent 核心模块，验证 DeepAgents 在 Windows 环境能跑通核心流程

- [ ] 在 `backend/app/agent/` 下实现 Lead Agent 工厂（`lead.py`）
- [ ] 在 `backend/app/agent/` 下定义 Sub-Agent（`subagents.py`）
- [ ] 在 `backend/app/tools/` 下实现 `web_search` 工具（`web_search.py`）
- [ ] 使用 LangChain `ChatOpenAI` 初始化模型（参数直接写在代码中，API key 从环境变量读取）
- [ ] 创建入口脚本运行 Agent 流程（可在 `backend/app/main.py` 或独立脚本）
- [ ] 验证 Lead → research-agent → report-agent 完整委派流程
- [ ] 输入一个研究问题，终端输出完整报告

**验收标准**：

- 运行入口脚本 → 输入问题 → 终端打印报告内容
- 全流程 < 3min，无报错
- 确认 `deepagents`、`langchain-openai`、`tavily` 在 Windows 环境兼容

**不包含**（后续 Phase 引入）：

- `config.yaml` 配置加载逻辑（Phase 1）
- `checkpointer` 持久化（Phase 1）
- `memory=["/AGENTS.md"]` 记忆（Phase 4）
- `with_fallbacks()` 多模型容灾（Phase 3）
- `LocalShellBackend` Sandbox（Phase 1）
- `skills/SKILL.md` 技能系统（Phase 1）
- FastAPI 路由和 API 端点（Phase 1）

### Phase 1: 项目骨架 + FastAPI API（1 周）

**目标**：把 Phase 0 的脚本封装成完整项目，基于 PRD 设计实现核心业务逻辑，通过 API 调用

- [ ] 搭建 monorepo 项目结构（backend/ frontend/ data/）
- [ ] `uv` + `pyproject.toml` 依赖管理
- [ ] `config.yaml` 配置加载（模型、搜索、Sandbox、持久化）
- [ ] FastAPI 主应用 + 基础路由
- [ ] `POST /api/threads` 创建会话
- [ ] `POST /api/threads/{id}/runs` 执行任务（同步返回）
- [ ] DeepAgents Lead Agent 集成（含 `checkpointer` + `recursion_limit`）
- [ ] 两个 Sub-Agent 完整定义（research-agent + report-agent）
- [ ] `task()` 委派流程端到端验证
- [ ] 单模型配置与运行（`with_fallbacks()` 预留接口，Phase 3 实现）
- [ ] Tavily `web_search` 工具 + SerpApi fallback 预留
- [ ] 文件系统 + Shell 工具（`LocalShellBackend`，`virtual_mode=True`）
- [ ] AGENTS.md 手动记忆（`memory=["/AGENTS.md"]`）
- [ ] 测试基础设施（pytest + 核心逻辑单元测试：agent 工厂、配置加载）

**验收标准**：

- `curl -X POST /api/threads/{id}/runs -d '{"content": "..."}'` → 返回报告内容
- 输入问题 → Lead Agent 委派 research-agent 搜索 → 委派 report-agent 撰写 → 返回完整报告
- 支持多轮对话（同一 thread 内，通过 `thread_id` 持久化）
- 模型配置通过 `config.yaml` 管理
- 核心逻辑（agent 工厂、配置加载）有对应单元测试

### Phase 2: 流式输出 + 前端（1 周）

**目标**：SSE 流式输出 + Streamlit 聊天界面，用户可直观看到 Agent 思考过程

- [ ] `GET /api/threads/{id}/runs/stream` SSE 流式输出（`agent.astream` + `text/event-stream`）
- [ ] Streamlit 聊天界面调用 FastAPI API
- [ ] 流式消息实时展示（token 级别更新）
- [ ] 报告文件写入与前端渲染
- [ ] 报告下载功能
- [ ] 消息历史持久化与展示
- [ ] Streamlit 界面增强（文件预览、任务状态指示）

**验收标准**：

- Streamlit 界面输入问题 → 实时看到 Agent 思考过程和中间步骤
- 生成的报告可在前端查看和下载
- SSE 流式输出延迟 < 1s（从 Agent 输出到界面展示）

### Phase 3: 体验增强（1 周）

**目标**：多模型切换、任务取消、界面完善

- [ ] `with_fallbacks()` 多模型容灾实现
- [ ] `GET /api/models` 返回所有可用模型和当前活跃模型
- [ ] `PUT /api/models/active` 手动切换活跃模型
- [ ] `POST /api/threads/{id}/runs/{run_id}/cancel` 取消正在执行的任务
- [ ] Streamlit 侧边栏模型选择器（下拉框，切换后持久化）
- [ ] 任务进度指示器（研究中/撰写中/完成）
- [ ] 执行日志与错误追踪
- [ ] LangSmith 集成（可选开关）

**验收标准**：

- 用户可手动切换模型，主模型失败时自动 fallback 到备用模型
- 运行中的任务可通过 API 和界面取消
- 长任务可通过 LangSmith 查看完整 trace

### Phase 4: 记忆与可观测性（1-2 周）

**目标**：跨线程记忆、HITL 中断、上下文管理

- [ ] 记忆查看/编辑 API（`GET /api/memory`、`PUT /api/memory`）
- [ ] 跨线程记忆（`CompositeBackend` + `Store`，`/memories/` 路径持久化）
- [ ] LLM 自动提取记忆（基础版：固定 prompt 对话结束后追加到 `/memories/extracted.md`）
- [ ] HITL 中断确认（`interrupt_on`，Phase 1 已有 checkpointer 基础）
- [ ] `POST /api/threads/{id}/runs/{run_id}/resume` 恢复被中断的任务
- [ ] `compact_conversation` 工具（手动压缩上下文，应对长任务）
- [ ] 记忆去重与冲突解决（进阶版）

**验收标准**：

- 跨会话保留用户偏好（`/memories/` 路径持久化）
- 对话结束后自动提取关键信息并写入记忆文件
- 用户可在关键操作（写文件、执行命令）前确认/拒绝
- 被中断的任务可恢复继续执行

---

## 8. 非功能性需求

### 8.1 性能

| 指标             | 目标          |
| ---------------- | ------------- |
| 简单问题响应时间 | < 10s         |
| 研究报告完成时间 | < 5min        |
| 内存占用（空闲） | < 500MB       |
| 并发会话数       | 1（个人使用） |

### 8.2 安全

- 文件操作通过 `FilesystemBackend(root_dir=...)` 限制在指定目录下，`virtual_mode=True` 禁止 `../` 和 `~/` 路径逃逸
- API 密钥通过环境变量管理，不硬编码
- 本地运行，不暴露公网端口
- `recursion_limit` 防止 agent 无限循环
- 外部工具（web_search、web_fetch）配置 `RetryPolicy(max_attempts=3)`

### 8.3 可维护性

- 类型提示覆盖所有公共接口（mypy 渐进式检查）
- 代码风格统一：`ruff check .`（lint）+ `ruff format .`（format）
- 类型检查：`mypy backend/app/`
- 单元测试覆盖核心逻辑：`uv run pytest`（agent 工厂、fallback、配置加载）
- 日志分级（INFO 记录流程，DEBUG 记录细节）
- 错误信息面向用户友好，面向开发者详细

---

## 9. 风险与缓解

| 风险                 | 影响             | 缓解措施                                   |
| -------------------- | ---------------- | ------------------------------------------ |
| DeepAgents API 变动  | 核心依赖不稳定   | 锁定版本号（`deepagents>=0.4,<0.6`，已验证 0.4.11），关注 changelog |
| Tavily 免费额度用完  | 搜索功能不可用   | SerpApi fallback                        |
| Windows 路径兼容问题 | 文件系统工具异常 | 统一使用 pathlib，测试 Windows 路径        |
| 模型输出质量差       | 研究结果不可用   | 支持手动切换模型 + 自动 fallback           |
| Agent 无限循环       | 资源耗尽         | `recursion_limit=50` 安全配置            |
| Context 窗口溢出     | 长任务失败       | DeepAgents 原生 summarization（默认开启）+ offloading |
| Streamlit 性能瓶颈   | 长任务界面卡顿   | Phase 1 已实现 SSE 流式输出                |
| mypy 与第三方库类型冲突 | 类型检查噪音，开发效率下降 | 用 `ignore_missing_imports` 跳过 deepagents/langchain 等模块 |
| uv lock 版本漂移     | 依赖版本不一致   | 提交 `uv.lock` 到版本管理，`uv sync --frozen` 确保一致性 |

---

## 10. 关键设计决策记录

| 决策           | 选项                                   | 选择                  | 理由                                                                   |
| -------------- | -------------------------------------- | --------------------- | ---------------------------------------------------------------------- |
| Agent 框架     | 自研 vs DeepAgents                     | DeepAgents            | 覆盖 70% 能力，避免重复造轮子                                          |
| 前端           | Next.js vs Streamlit                   | Streamlit (Phase 1)   | 快速验证，后续可替换                                                   |
| 记忆系统       | 自动提取 vs 手动文件                   | 手动文件 (Phase 1)    | DeepAgents 原生 `memory` 参数支持，实现简单                          |
| Sub-Agent 分工 | 单通用 vs 固定分工 vs 动态             | 固定分工              | context 隔离好，实现可控                                               |
| 搜索工具       | Tavily vs SerpApi vs Jina           | Tavily + SerpApi fallback | 免费额度 + 容灾                                                        |
| Shell 执行     | Git Bash vs WSL vs PowerShell          | Git Bash              | 已安装，轻量                                                           |
| 部署方式       | Docker vs 本地                         | 本地                  | Windows 环境，不需要 Docker                                            |
| 产物系统       | 完整 artifact vs 简单文件              | 简单文件              | 产物类型单一，无需复杂系统                                             |
| 执行模式       | 异步流式 vs 同步                       | SSE 流式 (Phase 1)    | LangGraph `astream` 开箱即用，用户体验好                             |
| 仓库结构       | 分离 vs monorepo                       | monorepo              | 个人项目，管理简单                                                     |
| API 实现       | LangSmith Agent Server vs FastAPI 自研 | FastAPI 自研          | 学习目的，理解 thread/run/checkpoint 完整生命周期                      |
| 模型切换       | 仅自动 fallback vs 用户选择 + fallback | 两层机制              | 兼顾容灾与用户控制权                                                   |
| Checkpointer   | MemorySaver vs AsyncSqliteSaver        | AsyncSqliteSaver      | 轻量持久化，重启不丢失会话状态                                         |
| Context 压缩   | 手动实现 vs DeepAgents 原生            | DeepAgents 原生       | 内置 `SummarizationMiddleware` 自动 offload + summarization，无需额外配置 |
| 模型初始化时机 | 传入字符串 vs 传入预配置实例            | 传入字符串            | `create_deep_agent(model="...")` 会立即初始化模型并校验 API key，需确保环境变量提前设置；Phase 1 使用 dummy key 兜底 |
| 开发顺序       | 先前端 vs 先 API vs 先 Agent 核心       | Agent 核心 → API → 前端 | Phase 0 纯脚本验证 Agent 能跑通，Phase 1 封装 FastAPI API，Phase 2 再加 Streamlit 前端，避免过早引入框架导致混乱 |
| Sandbox Backend  | LocalShellBackend vs FilesystemBackend | FilesystemBackend | 降低风险（避免 Windows 编码 Bug、Shell 安全）、简化配置 |
