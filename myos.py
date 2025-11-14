from __future__ import annotations

import os

from agno.os import AgentOS
from dotenv import load_dotenv

from agents import build_default_pipeline
from agents.asset.builder import build_asset_agent
from agents.behavior.builder import build_behavior_agent
from agents.conversation.builder import build_conversation_agent
from agents.fund_advice.builder import build_fund_advice_agent
from agents.socio_role.builder import build_socio_role_agent
from agents.summary.builder import build_summary_agent

load_dotenv(override=True)

# 统一初始化底层模型配置（通过环境变量控制）
os.environ.setdefault("AGNO_MODEL_ID", "qwen-turbo-latest")
os.environ.setdefault("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 实例化仓库已有的 Agent，方便在 AgentOS 中逐个调试
agents_suite = [
    build_socio_role_agent(),
    build_asset_agent(),
    build_behavior_agent(),
    build_summary_agent(),
    build_fund_advice_agent(),
    build_conversation_agent(),
]

# 保留一份默认流水线，可在调试时使用 pipeline.run(payload)
pipeline = build_default_pipeline()

agent_os = AgentOS(agents=agents_suite)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="myos:app", reload=True)
