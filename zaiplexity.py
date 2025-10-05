from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.os import AgentOS
from agno.tools.mcp import MCPTools
from agno.tools.mcp import StreamableHTTPClientParams
from agno.tools.mcp import StdioServerParameters
from agno.team.team import Team
import os
from agno.db.sqlite import SqliteDb

# Agent instructions
DEEP_RESEARCHER_INSTRUCTIONS = [
    "You are a deep research assistant. Use the available search tool when needed to find accurate and up-to-date information to help answer questions and provide comprehensive research support. Always provide thorough, well-researched responses. Note: The fetch tool is slow, so use it a maximum of 6 times per request."
]

FAST_AGENT_INSTRUCTIONS = [
    "You are a fast assistant. Provide quick, accurate responses to user queries. Use the available search tool when needed for up-to-date information. Note: The fetch tool is slow, so use it a maximum of 3 times per request."
]

VISUAL_AGENT_INSTRUCTIONS = [
    "You are an image analysis expert. Analyze images thoroughly and provide detailed insights about what you see. Focus on identifying objects, people, scenes, text, and any important details in the images."
]

# Determine the endpoint based on ZAI_CHINA_ENDPOINT environment variable
if os.getenv('ZAI_CHINA_ENDPOINT', 'false').lower() == 'true':
    ZAI_BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4"
    ZAI_MCP_URL = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
else:
    ZAI_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
    ZAI_MCP_URL = "https://api.z.ai/api/mcp/web_search_prime/mcp"


db = SqliteDb(
    db_file="agno.db",
    session_table="sessions",
    eval_table="eval_runs",
    memory_table="user_memories",
    metrics_table="metrics",
)


# Create MCP tools for Search
search_tools = MCPTools(
    transport="streamable-http",
    server_params=StreamableHTTPClientParams(
        url=ZAI_MCP_URL,
        headers={"Authorization": f"Bearer {os.getenv('ZAI_API_KEY')}"},
    ),
)

# Create MCP tools for Read Page
read_page_tools = MCPTools(
    transport="stdio",
    server_params=StdioServerParameters(command="uvx", args=["mcp-server-fetch"]),
)

# Deep Researcher Agent (using glm-4.6)
deep_researcher = Agent(
    name="Deep Researcher",
    model=OpenAILike(
        id="glm-4.6",
        api_key=os.getenv("ZAI_API_KEY"),
        base_url=ZAI_BASE_URL,
    ),
    instructions=DEEP_RESEARCHER_INSTRUCTIONS,
    tools=[search_tools, read_page_tools],
    db=db,
    enable_user_memories=True,
    enable_session_summaries=True,
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

# Fast Agent (using glm-4.5-air)
fast_agent = Agent(
    name="Fast Researcher",
    model=OpenAILike(
        id="glm-4.5-air",
        api_key=os.getenv("ZAI_API_KEY"),
        base_url=ZAI_BASE_URL,
    ),
    instructions=FAST_AGENT_INSTRUCTIONS,
    tools=[search_tools, read_page_tools],
    db=db,
    enable_user_memories=True,
    enable_session_summaries=True,
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

# Visual Agent (using glm-4.5v)
visual_agent = Agent(
    name="Visual Researcher",
    model=OpenAILike(
        id="glm-4.5v",
        api_key=os.getenv("ZAI_API_KEY"),
        base_url=ZAI_BASE_URL,
    ),
    instructions=VISUAL_AGENT_INSTRUCTIONS,
    db=db,
    enable_user_memories=True,
    enable_session_summaries=True,
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

agent_os = AgentOS(
    id="zaiplexity",
    description="A set of web researching agents for subscibers of the z.ai pro coding plan",
    agents=[deep_researcher, fast_agent, visual_agent],
)

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="zaiplexity:app", reload=True, port=8000)
