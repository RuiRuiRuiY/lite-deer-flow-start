"""Sub-Agent 定义：research-agent + report-agent"""

RESEARCH_AGENT_CONFIG = {
    "name": "research-agent",
    "description": "搜索互联网、提取网页内容、整理信息并写入工作文件",
    "system_prompt": (
        "你是一个研究专家。使用互联网搜索工具查找信息，提取关键内容，"
        "整理为结构化的研究笔记并写入工作文件。"
        "保持笔记简洁、准确、去重。"
    ),
    "tools": [],  # internet_search 将在工厂中注入
    "skills": ["./skills/research/"],
}

REPORT_AGENT_CONFIG = {
    "name": "report-agent",
    "description": "阅读研究文件，撰写结构化报告",
    "system_prompt": (
        "你是一个专业的报告撰写人。阅读研究笔记，按照报告结构撰写完整的分析报告。"
        "报告应包含：执行摘要、背景介绍、主要发现、详细分析、结论与建议、参考资料。"
        "使用 Markdown 格式，关键数据加粗。"
    ),
    "tools": [],  # 使用内置文件工具（read_file, write_file, edit_file）
    "skills": ["./skills/report/"],
}


def get_subagents(internet_search_tool, model) -> list[dict]:
    """返回 sub-agents 配置列表。

    Args:
        internet_search_tool: 已初始化的 internet_search 工具实例
        model: 模型实例，所有 sub-agent 共享同一个模型

    Returns:
        sub-agents 配置列表
    """
    research = RESEARCH_AGENT_CONFIG.copy()
    research["tools"] = [internet_search_tool]
    research["model"] = model

    report = REPORT_AGENT_CONFIG.copy()
    report["model"] = model

    return [research, report]
