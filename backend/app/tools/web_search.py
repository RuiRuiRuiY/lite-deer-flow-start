"""Web search tool: Tavily with mock mode fallback"""

import os
from typing import Literal

from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

from tavily import TavilyClient

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MOCK_RESULTS = [
    {
        "title": "模拟搜索结果 1 - 离线测试数据",
        "url": "https://example.com/result-1",
        "content": "这是 mock 模式的模拟搜索结果。实际开发中请设置 TAVILY_API_KEY 以获取真实数据。",
        "score": 0.95,
    },
    {
        "title": "模拟搜索结果 2 - 多来源测试",
        "url": "https://example.com/result-2",
        "content": "Mock 模式返回多条结果，模拟真实搜索引擎返回的内容多样性。",
        "score": 0.88,
    },
    {
        "title": "模拟搜索结果 3 - 内容完整性测试",
        "url": "https://example.com/result-3",
        "content": "每条 mock 结果包含 title、url、content、score 字段，与 Tavily API 返回格式对齐。",
        "score": 0.82,
    },
]


def _is_mock_mode() -> bool:
    """检测是否应使用 mock 模式。

    当 TAVILY_API_KEY 未设置时返回 True。
    """
    return not bool(os.getenv("TAVILY_API_KEY"))


@tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = True,
):
    """Run a web search. Returns mock results when TAVILY_API_KEY is not set."""
    if _is_mock_mode():
        return MOCK_RESULTS[:max_results]

    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
