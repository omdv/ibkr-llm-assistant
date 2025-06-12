"""Test script for MCP agent."""

import asyncio
import logging

from agents.ibkr import ibkr_agent_run
from settings import MySettings
from mcp_agent.app import MCPApp
from mcp_app import my_app
from rich.console import Console

config = MySettings()
logger = logging.getLogger(__name__)

async def agent_run(app: MCPApp) -> None:
  """Run the MCP agent."""
  async with app.run():
    result = await ibkr_agent_run(app)
    Console().print("\nResult:", result)

if __name__ == "__main__":
  loop = asyncio.new_event_loop()
  try:
    loop.run_until_complete(agent_run(my_app))
  except Exception as e:
    logger.exception("Error during execution", exc_info=e)
  finally:
    loop.close()
