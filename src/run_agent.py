"""Test script for MCP agent."""
from rich.console import Console
from rich.panel import Panel

from src.agents.ibkr import ibkr_agent_run
from src.mcp_app import my_app

async def run_agent() -> None:
  """Run the MCP agent."""
  async with my_app.run():
    result = await ibkr_agent_run(my_app)
    Console().print(Panel(result, title="Agent Result", border_style="green"))
