"""Test script for MCP agent."""
from rich.console import Console
from rich.panel import Panel
from src.agents.prompt import prompt_agent_run
from src.mcp_app import my_app

async def run_prompt(query: str) -> None:
  """Run the MCP agent."""
  async with my_app.run():
    result = await prompt_agent_run(my_app, query)
    Console().print(Panel(result, title="Prompt Result", border_style="green"))
