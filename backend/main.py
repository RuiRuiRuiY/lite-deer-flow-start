"""Lite-DeerFlow CLI 入口

用法: cd backend && python main.py
      配置文件: ../config.yaml (项目根目录)
"""

import asyncio
from pathlib import Path

from app.agent.lead import create_lead_agent
from app.config import load_config


async def main():
    # 加载配置（从项目根目录）
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        print("请从 config.example.yaml 复制并填写配置:")
        print(f"  cp config.example.yaml {config_path}")
        print(f"  或 copy config.example.yaml {config_path}")
        return

    print("加载配置...")
    config = load_config(str(config_path))

    # 创建 agent
    print("初始化 Agent...")
    agent = create_lead_agent(config)

    # 接收用户输入
    question = input("\n研究问题: ").strip()
    if not question:
        print("错误: 输入不能为空")
        return

    # 执行 agent 流程
    print("\n开始研究...")
    print("-" * 40)

    step_count = 0
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": question}]
    })

    # 打印最终报告
    print("-" * 40)
    print("\n最终报告:")
    print("=" * 60)
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
