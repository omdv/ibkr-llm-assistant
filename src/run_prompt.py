"""Run the prompt."""
from src.mcp_app import answer_query

async def run_prompt(query: str) -> None:
  """Run the MCP agent."""
  result = await answer_query(query)
  print(result)  # noqa: T201
