"""Telegram MCP server."""

from fastmcp import FastMCP
from loguru import logger
from src.servers.telegram.telegram_bot import TelegramBot

telegram = FastMCP("telegram")

@telegram.tool(name="send_message")
async def send_message(message: str) -> str:
  """Send a message to the Telegram bot.

  Args:
    message: The message to send to the user. Format using markdown.

  Returns:
    str: The status of the message.

  """
  bot = TelegramBot()
  try:
    bot.send_message(message)
  except Exception as e:
    logger.error("Error sending message: {}", str(e))
    return f"Error sending message: {str(e)!r}"
  return "Message sent"

if __name__ == "__main__":
  try:
    telegram.run(transport="stdio")
  except Exception as e:
    logger.error("MCP server error: {}", str(e))
    raise
