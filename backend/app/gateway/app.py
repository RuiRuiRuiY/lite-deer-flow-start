"""FastAPI 应用工厂"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。

    返回:
        配置好的 FastAPI 应用，包含 CORS 中间件和健康检查端点。
    """
    app = FastAPI(title="Lite-Deer-Flow")

    # CORS 中间件（本地开发允许所有来源）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 健康检查端点
    @app.get("/api/health")
    async def health_check():
        return {"status": "ok"}

    return app
