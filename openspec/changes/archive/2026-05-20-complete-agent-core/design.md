## Context

当前 `backend/app/agent/lead_agent.py` 是 Phase 0 原型：
- 模块级 `load_dotenv()` + 立即 `invoke()` 一个硬编码问题
- 只有一个 research-agent，缺少 report-agent
- 使用 DashScope API 硬编码，无配置驱动
- 无 FilesystemBackend（agent 无法读写文件）
- 无 skills（SKILL.md）系统
- 无配置加载逻辑

项目已有 `config.example.yaml`（刚创建，DashScope 默认），但无 `config.py` 加载器。

约束：
- Windows 本地环境，Python 3.13+
- DeepAgents >= 0.6.2 已安装
- 不使用 FastAPI、checkpointer、memory（后续 Phase）
- 使用 DashScope qwen-flash 作为默认模型

## Goals / Non-Goals

**Goals:**
- Agent 工厂模式：`create_lead_agent(config)` 返回可复用的 agent 实例
- 完整流程：Lead Agent → research-agent（搜索+写入）→ report-agent（读取+撰写）→ 输出报告
- 配置驱动：模型/搜索/backend/skills 全部从 `config.yaml` 读取
- 离线可测：无 Tavily API key 时自动启用 mock 模式
- CLI 入口：`python main.py` 输入问题 → 终端打印报告

**Non-Goals:**
- FastAPI / HTTP API（Phase 1）
- checkpointer / 会话持久化（Phase 1）
- AGENTS.md 记忆系统（Phase 4）
- with_fallbacks() 多模型容灾（Phase 3）
- web_fetch 独立工具（Tavily include_raw_content 替代）
- 单元测试基础设施（后续 Phase）

## Decisions

### D1: FilesystemBackend 替代 LocalShellBackend

**决策**: 使用 `FilesystemBackend(root_dir="data/workspace", virtual_mode=True)`

**理由**:
- 研究+写报告流程不需要 shell 执行
- 避免 Windows GBK/UTF-8 编码 Bug（GitHub Issue #2311）
- 无 shell 绕过路径限制的安全风险
- 配置更简单（仅 root_dir + virtual_mode，无 timeout/max_output_bytes）

**替代方案**: 保留 LocalShellBackend — 被否决，因风险大于收益。

### D2: 模型使用 init_chat_model 而非 ChatOpenAI

**决策**: 使用 `langchain.chat_models.init_chat_model(model_provider="openai", ...)`

**理由**:
- 当前原型已验证 init_chat_model 与 DashScope 兼容
- 统一 OpenAI 兼容接口，后续切 DeepSeek 只需改 config
- 比 ChatOpenAI 更灵活（provider 参数化）

### D3: 配置加载使用 PyYAML 直接解析

**决策**: `config.py` 用 `yaml.safe_load()` 加载 YAML，返回 dict

**理由**:
- 简单直接，无额外依赖（PyYAML 已广泛使用）
- 不需要 Pydantic 验证（Phase 1 可加）
- dict 足够工厂函数使用

### D4: Mock 模式自动检测 + 显式开关

**决策**: `internet_search()` 在 `TAVILY_API_KEY` 未设置时自动返回 mock 数据；config.yaml 中 `search.mock: true` 可强制启用

**理由**:
- 开发者无 API key 时也能跑通流程
- 显式开关方便调试和 CI
- mock 数据格式对齐 Tavily 返回结构

### D5: Agent 工厂接收 config dict 而非路径

**决策**: `create_lead_agent(config: dict)` 而非 `create_lead_agent(config_path: str)`

**理由**:
- 调用方负责加载配置，工厂专注组装
- 便于测试（直接传 dict）
- 配置加载逻辑可独立演进

### D6: Sub-agent 不显式传 model

**决策**: subagents 定义中不传 `model` 参数，让 DeepAgents 自动使用 lead agent 的模型

**理由**:
- 减少重复配置
- 两个 sub-agent 和 lead agent 使用同一模型是预期行为
- 如不自动继承，后续可显式传入

## Risks / Trade-offs

| 风险 | 缓解 |
|------|------|
| DeepAgents sub-agent 不继承 lead agent model | 显式传入同一个 model 实例作为兜底 |
| Skills 路径解析问题（相对 cwd vs root_dir） | 使用相对于 `backend/` 的路径，测试验证 |
| qwen-flash 上下文窗口较小 | 研究笔记保持简洁，Phase 3 加 summarization |
| Tavily mock 数据过于简单，agent 行为失真 | mock 数据包含多条目、多来源，模拟真实搜索返回 |
| FilesystemBackend root_dir 不存在时崩溃 | 工厂函数中 `Path(root_dir).mkdir(parents=True, exist_ok=True)` |
