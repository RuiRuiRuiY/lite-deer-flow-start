"""YAML 配置加载器"""

import os
from pathlib import Path

import yaml


def load_config(path: str) -> dict:
    """加载 YAML 配置文件，返回 dict。

    Args:
        path: config.yaml 文件路径（绝对路径或相对于 cwd）

    Returns:
        配置字典，包含 models, search, sandbox, skills 等段

    Raises:
        FileNotFoundError: 配置文件不存在
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_model_config(config: dict) -> dict:
    """从配置中提取模型配置（primary 段）。

    Returns:
        {provider, model, base_url, api_key}
    """
    model_cfg = config["models"]["primary"]
    return {
        "provider": model_cfg["provider"],
        "model": model_cfg["model"],
        "base_url": model_cfg["base_url"],
        "api_key": os.getenv(model_cfg["api_key_env"]),
    }


def get_sandbox_config(config: dict) -> dict:
    """从配置中提取 sandbox 配置。

    Returns:
        {type, virtual_mode}
    """
    sandbox = config.get("sandbox", {})
    return {
        "type": sandbox.get("type", "filesystem"),
        "virtual_mode": sandbox.get("virtual_mode", True),
    }


def get_search_config(config: dict) -> dict:
    """从配置中提取搜索配置。

    Returns:
        {primary, mock}
    """
    search = config.get("search", {})
    # 自动检测：如果 API key 不存在，强制 mock
    tavily_key_env = search.get("tavily_api_key_env", "TAVILY_API_KEY")
    has_api_key = bool(os.getenv(tavily_key_env))
    explicit_mock = search.get("mock", False)

    return {
        "primary": search.get("primary", "tavily"),
        "mock": explicit_mock or not has_api_key,
    }
