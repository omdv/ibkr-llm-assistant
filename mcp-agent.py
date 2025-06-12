"""Test script for MCP agent."""

import asyncio
import logging

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.config import (
  Settings,
  LoggerSettings,
  MCPSettings,
  MCPServerSettings,
  AnthropicSettings,
)
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from settings import MCPAgentSettings

config = MCPAgentSettings()
logger = logging.getLogger(__name__)

app = MCPApp(
  name="calendar_test",
  settings=Settings(
    execution_engine="asyncio",
    logger=LoggerSettings(
      transports=["console", "file"],
      level=config.verbose_level,
      path="logs/mcp-agent.jsonl",
    ),
    mcp=MCPSettings(
      servers={
        "calendar": MCPServerSettings(
          command="python",
          args=["-m", "servers.calendar.server"],
          env={
            "SERVER_TIMEZONE": config.server_timezone,
          },
        ),
        "fmp": MCPServerSettings(
          command="python",
          args=["-m", "servers.fmp.server"],
          env={
            "SERVER_TIMEZONE": config.server_timezone,
            "QUOTES_API_KEY": config.quotes_api_key,
          },
        ),
        "ibkr": MCPServerSettings(
          command="python",
          args=["-m", "servers.ibkr.server"],
          env={
            "IB_GATEWAY_HOST": config.ib_gateway_host,
            "IB_GATEWAY_PORT": config.ib_gateway_port,
            "IB_COMMAND_SERVER_PORT": config.ib_command_server_port,
            "TELEGRAM_BOT_TOKEN": config.telegram_bot_token,
            "TELEGRAM_ALLOWED_USER_ID": config.telegram_allowed_user_id,
            "TELEGRAM_APPROVAL_TIMEOUT": str(config.telegram_approval_timeout),
          },
        ),
      },
    ),
    anthropic=AnthropicSettings(
      api_key=config.anthropic_api_key,
      default_model=config.anthropic_model,
      max_tokens=config.anthropic_model_max_tokens,
    ),
  ),
)

async def run() -> str:
  """Run the MCP agent."""
  async with app.run():
    agent = Agent(
      name="calendar_agent",
      instruction="""
      You are a helpful assistant that supports the trading of stocks and options.
      You can access the calendar to get today's date and exchange sessions.
      You can access the financial modeling prep server to get the important upcoming events.
      You can access the IBKR server to get the current positions and to place trades.
      """,
      server_names=["calendar", "fmp", "ibkr"],
    )

    llm = AnthropicAugmentedLLM(agent)
    return await llm.generate_str(
      "List all available tools, then get the price of SPX and get my positions",
      request_params=RequestParams(maxTokens=1024),
    )

def main() -> None:
  """Run the MCP agent."""
  loop = asyncio.new_event_loop()
  try:
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(run())
    print("\nResult:", result)
  except Exception as e:
    logger.exception("Error during execution", exc_info=e)
  finally:
    loop.close()

if __name__ == "__main__":
  main()
