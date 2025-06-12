"""IBKR MCP client - Recommended version for interactive chat."""

import asyncio
from loguru import logger

from rich.console import Console
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM

from mcp_app import my_app

# Agent definition remains the same.
chat_agent = Agent(
  name="chat_agent",
  instruction="""
  You are a helpful assistant that supports the trading of stocks and options.
  You have a set of tools that you can use to help the user.
  """,
  server_names=["calendar", "fmp", "ibkr"],
)

# The core chat logic is now clean and simple.
# It has no responsibility for shutdown; it just runs the chat.
async def chat_run(app: MCPApp) -> None:
  """Run the main chat agent loop."""
  async with app.run():
    llm = await chat_agent.attach_llm(AnthropicAugmentedLLM)
    llm.memory = True

    await asyncio.sleep(1)
    Console().print(
      "\n[bold green]Chat session started.[/bold green]"
      "\nType 'exit' or press Ctrl+C to quit.")
    while True:
      try:
        query = await asyncio.to_thread(input, "\nYou: ")
        query = query.strip()

        if query.lower() == "exit":
          Console().print(
            "\n[bold yellow]'exit' command received. Shutting down...[/bold yellow]")
          break
        if not query:
          continue

        result = await llm.generate_str(message=query)
        Console().print(f"\n[cyan]Assistant:[/cyan] {result}")

      except (KeyboardInterrupt, EOFError):
        break
      except Exception as e:
        logger.exception("Error during chat interaction", exc_info=e)
        Console().print("[bold red]An error occurred. Please try again.[/bold red]")


if __name__ == "__main__":
  loop = asyncio.get_event_loop()
  main_task = None

  try:
    main_task = loop.create_task(chat_run(my_app))
    loop.run_until_complete(main_task)
  except KeyboardInterrupt:
    Console().print("\n[bold yellow]Keyboard interrupt. Shutting down...[/bold yellow]")
  finally:
    # gracefully shutdown the chat
    if main_task:
      main_task.cancel()
    tasks = asyncio.all_tasks(loop=loop)
    for task in tasks:
      task.cancel()
    group = asyncio.gather(*tasks, return_exceptions=True)
    loop.run_until_complete(group)
    loop.close()
