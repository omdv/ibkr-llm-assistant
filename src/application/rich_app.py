"""Rich-based UI for the MCP client."""
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.style import Style
from loguru import logger

from mcp_client import MCPClient
from src.utilities import setup_logging

class RichApp:
  """Simple Rich-based chat application."""

  def __init__(self, mcp_client: MCPClient) -> None:
    """Initialize the app."""
    self.mcp_client = mcp_client
    self.console = Console()
    self.running = False
    setup_logging()

  def display_message(self, message: str, sender: str = "assistant") -> None:
    """Display a message with appropriate styling."""
    style = Style(color="magenta") if sender == "user" else Style(color="green")
    border_style = "magenta" if sender == "user" else "green"

    panel = Panel(
      message,
      border_style=border_style,
      style=style,
      expand=False,
      padding=(1, 2),
    )
    self.console.print(panel)
    # Ensure a newline after each message
    self.console.print()

  async def process_input(self, user_input: str) -> None:
    """Process user input and display response."""
    user_echo = False
    if user_echo:
      # Display and save user message
      self.display_message(user_input, "user")

    # Get and display response
    response = await self.mcp_client.process_query(user_input)
    self.display_message(response, "assistant")

  async def run(self) -> None:
    """Run the application."""
    self.running = True

    # Clear screen and show welcome message
    self.console.clear()
    self.console.print(
      Panel(
        "Welcome to IBKR MCP Chat\nPress Ctrl+C to exit",
        style="bold white",
        border_style="blue",
      ),
    )
    self.console.print()  # Add extra newline for spacing

    # Connect to server
    await self.mcp_client.connect_to_server()
    await asyncio.sleep(1)

    try:
      while self.running:
        try:
          # Get user input with proper prompt handling
          self.console.print()  # Ensure clean line before prompt
          user_input = Prompt.ask("\n[bold magenta]You[/bold magenta]")
          if user_input.lower() in ("exit", "quit"):
              break

          # Process the input
          await self.process_input(user_input)

        except KeyboardInterrupt:
          self.running = False
          break
        except Exception as e:
          logger.error("Error processing input: {}", str(e))
          self.console.print(f"[red]Error: {str(e)!s}[/red]")
          self.console.print()  # Add spacing after error

    finally:
      # Cleanup
      await self.mcp_client.cleanup()
      self.console.print("\n[yellow]Goodbye![/yellow]")
