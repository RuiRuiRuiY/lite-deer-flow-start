"""Gateway 数据存储层

内存 ThreadStore，提供 CRUD 和消息追加，预留持久化接口。
"""

import asyncio
from datetime import UTC, datetime

from app.gateway.schemas import Message, Thread


class ThreadStore:
    """内存会话存储，使用 asyncio.Lock 保证异步安全。"""

    def __init__(self) -> None:
        self._threads: dict[str, Thread] = {}
        self._lock = asyncio.Lock()

    async def create(self, title: str) -> Thread:
        """创建新会话。"""
        async with self._lock:
            thread = Thread(title=title)
            self._threads[thread.id] = thread
            await self._save()
            return thread

    async def get(self, id: str) -> Thread | None:
        """按 ID 获取会话。"""
        async with self._lock:
            thread = self._threads.get(id)
            if thread is not None:
                await self._load()
            return thread

    async def list(self) -> list[Thread]:
        """列出所有会话，按 updated_at 降序。"""
        async with self._lock:
            await self._load()
            return sorted(
                self._threads.values(),
                key=lambda t: t.updated_at,
                reverse=True,
            )

    async def delete(self, id: str) -> bool:
        """删除会话，存在返回 True，否则 False。"""
        async with self._lock:
            if id in self._threads:
                del self._threads[id]
                await self._save()
                return True
            return False

    async def add_message(self, thread_id: str, message: Message) -> Thread | None:
        """追加消息到会话，更新 updated_at。"""
        async with self._lock:
            thread = self._threads.get(thread_id)
            if thread is None:
                return None
            thread.messages.append(message)
            thread.updated_at = datetime.now(UTC)
            await self._save()
            return thread

    # --- 持久化占位方法（Phase 4 实现） ---

    async def _save(self) -> None:
        """持久化存储（当前为空操作）。"""
        pass

    async def _load(self) -> None:
        """从持久化存储加载（当前为空操作）。"""
        pass
