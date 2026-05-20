## 1. 基础设施

- [x] 1.1 在 `backend/pyproject.toml` 中添加 `pyyaml>=6.0` 依赖
- [x] 1.2 运行 `uv sync` 安装新依赖
- [x] 1.3 修复 `.env.example` 中 `DASHSCOP_BASE_URL` 拼写为 `DASHSCOPE_BASE_URL`
- [x] 1.4 更新 `config.example.yaml` 模型默认值从 DeepSeek 改为 DashScope（qwen-flash）

## 2. 配置加载

- [x] 2.1 创建 `backend/app/config.py`，实现 `load_config(path: str) -> dict`
- [x] 2.2 实现模型配置提取（provider, model, base_url, api_key_env → os.getenv）
- [x] 2.3 实现 sandbox 配置提取（type, virtual_mode）
- [x] 2.4 实现搜索配置提取（primary, mock 标志）

## 3. Sub-Agents 定义

- [x] 3.1 创建 `backend/app/agent/subagents.py`
- [x] 3.2 定义 research-agent（name, description, system_prompt, tools=[internet_search], skills）
- [x] 3.3 定义 report-agent（name, description, system_prompt, tools=[], skills）

## 4. Skills 文件

- [x] 4.1 创建 `backend/app/skills/research/SKILL.md`（按 PRD §4.6）
- [x] 4.2 创建 `backend/app/skills/report/SKILL.md`（按 PRD §4.6）

## 5. Agent 工厂

- [x] 5.1 创建 `backend/app/agent/lead.py`，实现 `create_lead_agent(config: dict)`
- [x] 5.2 集成 FilesystemBackend（root_dir="data/workspace", virtual_mode=True）
- [x] 5.3 集成 init_chat_model 从 config 创建模型
- [x] 5.4 集成 subagents 列表（从 subagents.py 导入）
- [x] 5.5 集成 skills 路径（research + report）
- [x] 5.6 集成 LEAD_AGENT_PROMPT 系统提示词
- [x] 5.7 确保 workspace 目录在工厂初始化时自动创建

## 6. 工具增强

- [x] 6.1 修改 `backend/app/tools/web_search.py`：`include_raw_content` 默认值改为 `True`
- [x] 6.2 添加 mock 模式：无 TAVILY_API_KEY 或 config.mock=true 时返回模拟结果
- [x] 6.3 mock 结果至少包含 3 条，格式对齐 Tavily（title, url, content, score）

## 7. CLI 入口

- [x] 7.1 修改 `backend/main.py` 为异步 CLI 入口
- [x] 7.2 加载 config.yaml（从 backend/ 目录）
- [x] 7.3 调用 create_lead_agent 创建 agent
- [x] 7.4 接收用户输入 → ainvoke → 打印最终报告
- [x] 7.5 处理空输入和异常情况的错误提示

## 8. 清理

- [x] 8.1 删除 `backend/app/agent/lead_agent.py`（被 lead.py 取代）
- [x] 8.2 从 backend/ 目录复制 config.example.yaml 为 config.yaml（用户需自行填写 API key）
