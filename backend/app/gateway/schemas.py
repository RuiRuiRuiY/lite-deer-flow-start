"""Gateway 数据模型定义

Thread、Message 及 API 请求/响应的 Pydantic schema。
"""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Message(BaseModel):
    """单条对话消息。"""

    role: str = Field(..., description="消息角色: user / assistant / system")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Thread(BaseModel):
    """会话线程，包含消息历史。"""

    id: str = Field(default_factory=lambda: f"thread_{uuid4().hex[:8]}")
    title: str = Field(..., min_length=1)
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CreateThreadRequest(BaseModel):
    """创建会话请求。"""

    title: str = Field(..., min_length=1, description="会话标题")


class ThreadResponse(BaseModel):
    """单线程完整响应（含消息）。"""

    id: str
    title: str
    messages: list[Message]
    created_at: datetime
    updated_at: datetime


class ThreadSummary(BaseModel):
    """线程摘要（列表用，不含完整消息）。"""

    id: str
    title: str
    updated_at: datetime


class ThreadListResponse(BaseModel):
    """线程列表响应。"""

    threads: list[ThreadSummary]


class RunRequest(BaseModel):
    """执行任务请求。"""

    content: str = Field(..., min_length=1, description="研究问题或任务内容")


class RunResponse(BaseModel):
    """任务执行响应。"""

    id: str = Field(default_factory=lambda: f"run_{uuid4().hex[:8]}")
    status: str = Field(..., description="completed / running / failed")
    result: str = Field(default="", description="执行结果")
    artifacts: list[str] = Field(default_factory=list, description="生成的文件路径列表")
