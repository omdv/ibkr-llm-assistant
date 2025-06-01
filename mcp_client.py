"""IBKR MCP client."""
import os
from anthropic import Anthropic
from loguru import logger
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.utilities import Settings, setup_logging

setup_logging()

class MCPClient:
  """IBKR MCP client."""

  def __init__(self, settings: Settings) -> None:
    """Initialize the MCP client."""
    self.settings = settings
    self.session: ClientSession | None = None
    self.exit_stack = AsyncExitStack()
    self.anthropic = Anthropic(api_key=settings.anthropic_api_key)
    self.message_history = []

  async def connect_to_server(self) -> None:
    """Connect to an MCP server."""
    server_params = StdioServerParameters(
      command="python",
      args=[self.settings.mcp_server_script],
      env=os.environ,
    )

    stdio_transport =\
      await self.exit_stack.enter_async_context(stdio_client(server_params))
    self.stdio, self.write = stdio_transport
    self.session =\
      await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

    await self.session.initialize()

    # List available tools
    response = await self.session.list_tools()
    tools = response.tools
    logger.debug("Connected to server with tools: {}", [tool.name for tool in tools])

  async def process_query(self, query: str) -> str:
    """Process a query using Claude and available tools."""
    logger.debug("Processing query: {}", query)
    self.message_history.append({
      "role": "user",
      "content": query,
    })

    messages = self.message_history.copy()

    response = await self.session.list_tools()
    available_tools = [{
      "name": tool.name,
      "description": tool.description,
      "input_schema": tool.inputSchema,
    } for tool in response.tools]

    final_text = []
    while True:
      # Get response from Claude
      response = self.anthropic.messages.create(
        model=self.settings.chat_model,
        max_tokens=self.settings.chat_model_max_tokens,
        messages=messages,
        tools=available_tools,
      )

      # Process all content from the response
      assistant_message_content = []
      has_tool_calls = False

      for content in response.content:
        if content.type == "text":
          final_text.append(content.text)
          assistant_message_content.append(content)
        elif content.type == "tool_use":
          has_tool_calls = True
          tool_name = content.name
          tool_args = content.input
          logger.debug("Calling tool {}", tool_name)

          try:
            # Execute tool call
            result = await self.session.call_tool(tool_name, tool_args)
            logger.debug("Tool result: {}", result)
            final_text.append(f"[tool][yellow]{result.content}[/yellow][/tool]")

            assistant_message_content.append(content)
            messages.append({
              "role": "assistant",
              "content": assistant_message_content,
            })
            messages.append({
              "role": "user",
              "content": [
                {
                  "type": "tool_result",
                  "tool_use_id": content.id,
                  "content": result.content,
                },
              ],
            })
          except Exception as e:
            error_msg = f"[error]Error executing tool {tool_name}: {str(e)!s}[/error]"
            logger.error(error_msg)
            final_text.append(error_msg)

      # If no tool calls were made, we're done
      if not has_tool_calls:
        messages.append({
          "role": "assistant",
          "content": assistant_message_content,
        })
        self.message_history = messages
        break
    return "\n".join(final_text)

  async def cleanup(self) -> None:
    """Cleanup resources."""
    await self.exit_stack.aclose()
