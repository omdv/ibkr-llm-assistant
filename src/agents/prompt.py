"""IBKR agent definition."""

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm import RequestParams

from src.settings import MySettings

config = MySettings()

async def prompt_agent_run(app: MCPApp, query: str) -> str:
  """Run the MCP agent."""
  async with app.run():
    agent = Agent(
      name="ibkr_agent",
      instruction="""
      You are a helpful assistant that supports the trading of stocks and options.
      You can access the calendar to get today's date and exchange sessions.
      You can access the 3rd party financial APIs to get the upcoming economic events.
      You can access the IBKR server to get the current positions and to place trades.
      You can access the Telegram server to send messages to the user.
      """,
      server_names=["calendar", "fmp", "ibkr", "telegram"],
    )

    llm = AnthropicAugmentedLLM(agent)

    return await llm.generate_str(
      query,
      request_params=RequestParams(maxTokens=config.anthropic_model_max_tokens),
    )
