## Why

Phase 0 的 `lead_agent.py` 是一次性原型：模块级直接运行、只有一个 research-agent、没有 report-agent、没有 FilesystemBackend、没有配置驱动。需要将其重构为可复用的 Agent 工厂，并通过 CLI 跑通"研究→写报告"完整流程，作为 Phase 1 FastAPI 的基础。

## What Changes

- **重构** `lead_agent.py` 为 `lead.py` Agent 工厂（`create_lead_agent(config)`）
- **新增** `subagents.py` 定义 research-agent + report-agent
- **新增** `config.py` YAML 配置加载
- **新增** `skills/research/SKILL.md` 和 `skills/report/SKILL.md`
- **新增** FilesystemBackend 集成（纯文件操作，无 shell 执行）
- **新增** mock 搜索模式（无 API key 时离线测试）
- **修改** `main.py` 为异步 CLI 入口
- **删除** `lead_agent.py` 一次性原型
- **修复** `.env.example` 环境变量拼写不一致（`DASHSCOP_BASE_URL` → `DASHSCOPE_BASE_URL`）
- **更新** `config.example.yaml` 模型默认值从 DeepSeek 改为 DashScope

## Capabilities

### New Capabilities

- `agent-core`: Agent 工厂（Lead Agent + research-agent + report-agent），含 FilesystemBackend 和 skills 集成
- `config-system`: YAML 配置加载（模型、搜索、sandbox、skills 路径）
- `cli-workflow`: CLI 入口跑通完整 agent 流程（输入问题 → 研究 → 写报告 → 输出）
- `mock-search`: 无 Tavily API key 时返回模拟搜索结果，支持离线调试

### Modified Capabilities

<!-- 无现有 spec 需要修改 -->

## Impact

- **新增文件**: `backend/app/agent/lead.py`, `backend/app/agent/subagents.py`, `backend/app/config.py`, `backend/app/skills/research/SKILL.md`, `backend/app/skills/report/SKILL.md`
- **修改文件**: `backend/main.py`, `backend/app/tools/web_search.py`, `backend/pyproject.toml`
- **删除文件**: `backend/app/agent/lead_agent.py`
- **依赖新增**: `pyyaml>=6.0`
- **不影响**: FastAPI、checkpointer、AGENTS.md 记忆、with_fallbacks()（后续 Phase 引入）
