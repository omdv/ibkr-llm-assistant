"""Entry point for the MCP client application."""
import asyncio
import argparse
from rich.console import Console

from src.run_agent import run_agent
from src.run_chat import run_chat
from src.run_prompt import run_prompt

def main() -> None:
  """Launch the application."""
  parser = argparse.ArgumentParser(description="IBKR MCP Client")
  parser.add_argument(
    "--chat",
    action="store_true",
    help="Chat with LLM in the CLI")
  parser.add_argument(
    "--agent",
    action="store_true",
    help="Run the MCP agent")
  parser.add_argument(
    "--prompt",
    type=str,
    help="Run the MCP prompt")

  args = parser.parse_args()
  if not any(vars(args).values()):
    parser.print_help()
    return

  loop = asyncio.get_event_loop()
  main_task = None

  try:
    if args.chat:
      main_task = loop.create_task(run_chat())
    if args.agent:
      main_task = loop.create_task(run_agent())
    if args.prompt:
      main_task = loop.create_task(run_prompt(args.prompt))

    if main_task:
      loop.run_until_complete(main_task)
  except KeyboardInterrupt:
    Console().print("\n[bold yellow]Keyboard interrupt. Shutting down...[/bold yellow]")
  finally:
    if main_task:
      main_task.cancel()

    tasks = asyncio.all_tasks(loop=loop)
    [task.cancel() for task in tasks]

    group = asyncio.gather(*tasks, return_exceptions=True)
    loop.run_until_complete(group)
    loop.close()

if __name__ == "__main__":
  main()
