"""Lead Agent 工厂：创建并配置完整的 Deep Agent"""

from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import init_chat_model

from app.agent.subagents import get_subagents
from app.config import get_model_config, get_sandbox_config
from app.prompts.lead_agent_prompt import LEAD_AGENT_PROMPT
from app.tools.web_search import internet_search


def create_lead_agent(config: dict):
    """创建 Lead Agent 实例。

    Args:
        config: 配置字典（由 config.load_config() 返回）

    Returns:
        配置好的 Deep Agent，含 lead agent + 2 sub-agents + FilesystemBackend + skills
    """
    # 1. 创建模型
    model_cfg = get_model_config(config)
    model = init_chat_model(
        model=model_cfg["model"],
        model_provider=model_cfg["provider"],
        base_url=model_cfg["base_url"],
        api_key=model_cfg["api_key"],
        timeout=30,
    )

    # 2. 创建 FilesystemBackend
    sandbox_cfg = get_sandbox_config(config)
    root_dir = Path("data/workspace")
    root_dir.mkdir(parents=True, exist_ok=True)

    backend = FilesystemBackend(
        root_dir=str(root_dir),
        virtual_mode=sandbox_cfg["virtual_mode"],
    )

    # 3. 获取 sub-agents（注入 internet_search 工具 + model）
    subagents = get_subagents(internet_search, model)

    # 4. 获取 skills 路径
    skills_paths = config.get("skills", {}).get("paths", [])

    # 6. 创建 agent
    agent = create_deep_agent(
        model=model,
        system_prompt=LEAD_AGENT_PROMPT,
        backend=backend,
        subagents=subagents,
        skills=skills_paths,
    )

    return agent
