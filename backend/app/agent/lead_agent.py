import os
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

from app.tools.web_search import internet_search
from app.prompts.lead_agent_prompt import LEAD_AGENT_PROMPT

model=init_chat_model(
    model="qwen-flash",
    model_provider="openai",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOP_BASE_URL"),
    timeout=10,
)

research_subagent = {
    "name": "research-agent",
    "description": "Used to research more in depth questions",
    "system_prompt": "You are a great researcher",
    "tools": [internet_search],
    "model": model
}

lead_agent = create_deep_agent(
    model=model,
    system_prompt=LEAD_AGENT_PROMPT,
    subagents=[
        research_subagent
    ]
)

result = lead_agent.invoke({"messages": [{"role": "user", "content": "特朗普访华的最新日期"}]})

# Print the agent's response
print(result["messages"][-1].content)