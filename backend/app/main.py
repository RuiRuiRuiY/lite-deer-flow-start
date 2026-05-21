"""Uvicorn 入口脚本

用法: uv run --directory backend uvicorn app.main:app --host 127.0.0.1 --port 8000
      或:   uv run --directory backend python -m uvicorn app.main:app
"""

from pathlib import Path

import yaml

from app.gateway.app import create_app

# 创建 FastAPI 应用实例
app = create_app()


def _load_server_config() -> tuple[str, int]:
    """从 config.yaml 读取 server.host / server.port。

    返回:
        (host, port) 元组，缺失时使用默认值。
    """
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    default_host = "127.0.0.1"
    default_port = 8000

    if not config_path.exists():
        return default_host, default_port

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        server = config.get("server", {})
        host = server.get("host", default_host)
        port = server.get("port", default_port)
        return host, port
    except Exception:
        return default_host, default_port


if __name__ == "__main__":
    import uvicorn

    host, port = _load_server_config()
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
