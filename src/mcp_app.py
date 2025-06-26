"""Define the MCP application."""

from mcp_agent.app import MCPApp
from mcp_agent.config import (
  Settings,
  MCPSettings,
  MCPServerSettings,
  AnthropicSettings,
)
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm import RequestParams

from src.settings import MySettings

config = MySettings()

my_app = MCPApp(
  name="calendar_test",
  settings=Settings(
    mcp=MCPSettings(
      servers={
        "calendar": MCPServerSettings(
          command="python",
          args=["-m", "src.servers.calendar.server"],
          env={
            "SERVER_TIMEZONE": config.server_timezone,
          },
        ),
        "telegram": MCPServerSettings(
          command="python",
          args=["-m", "src.servers.telegram.server"],
          env={
            "TELEGRAM_BOT_TOKEN": config.telegram_bot_token,
            "TELEGRAM_ALLOWED_USER_ID": config.telegram_allowed_user_id,
          },
        ),
        "fmp": MCPServerSettings(
          command="python",
          args=["-m", "src.servers.fmp.server"],
          env={
            "SERVER_TIMEZONE": config.server_timezone,
            "QUOTES_API_KEY": config.quotes_api_key,
          },
        ),
        "ibkr": MCPServerSettings(
          command="python",
          args=["-m", "src.servers.ibkr.server"],
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

async def answer_query(query: str) -> str:
  """Answer a query using the MCP app."""
  async with my_app.run():
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
