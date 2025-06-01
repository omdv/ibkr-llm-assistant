"""Entry point for the MCP client application."""
import asyncio
import argparse
import uvicorn
from rich.console import Console
from src.utilities import Settings
from src.application import RichApp

from mcp_client import MCPClient

async def main() -> None:
  """Launch the application."""
  parser = argparse.ArgumentParser(description="IBKR MCP Client")
  parser.add_argument(
    "--query",
    type=str,
    help="Run a single prompt and exit")
  parser.add_argument(
    "--cli",
    action="store_true",
    help="Chat with LLM in the CLI")
  parser.add_argument(
    "--web",
    action="store_true",
    help="Run scheduled prompts in the web interface")

  args = parser.parse_args()

  # If no arguments provided, show help
  if len(vars(args)) == 0:
    parser.print_help()
    return

  settings = Settings()
  mcp_client = MCPClient(settings)

  if args.query:
    await mcp_client.connect_to_server()
    result = await mcp_client.process_query(args.query)
    Console().print(result)
    await mcp_client.cleanup()
  elif args.cli:
    app = RichApp(mcp_client)
    await app.run()
    await mcp_client.cleanup()
  elif args.web:
    uvicorn.run(
      "src.web.app:app",
      host="127.0.0.1",
      port=settings.web_port,
      reload=True,
      reload_dirs=["src/web"],
    )
  else:
    parser.print_help()

if __name__ == "__main__":
  asyncio.run(main())
