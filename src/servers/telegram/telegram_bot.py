"""Telegram bot for sending messages."""

import asyncio
from loguru import logger
from telegram.ext import Application
from src.servers.telegram.settings import Settings


class TelegramBot:
  """Telegram bot for sending messages."""

  def __init__(self) -> None:
    """Initialize the bot."""
    self.settings = Settings()
    self.token = self.settings.telegram_bot_token
    self.chat_id = self.settings.telegram_allowed_user_id
    self._task = None

    # Initialize bot
    self.app = Application.builder().token(self.token).build()

  async def start(self) -> None:
    """Start the bot properly."""
    await self.app.initialize()
    await self.app.start()
    await self.app.updater.start_polling()

  async def stop(self) -> None:
    """Stop the bot."""
    if self.app.updater:
      await self.app.updater.stop()
    await self.app.stop()
    await self.app.shutdown()

  def send_message(
    self,
    message: str,
    parse_mode: str = "Markdown",
  ) -> None:
    """Send a message to the user, synchronously.

    Args:
      message: The message to send
      parse_mode: The parse mode for the message (default: Markdown)

    """
    async def _send() -> None:
      try:
        await self.start()
        await self.app.bot.send_message(
          chat_id=self.chat_id,
          text=message,
          parse_mode=parse_mode,
        )
      except Exception as e:
        logger.error("Error sending message: {}", str(e))
      finally:
        await self.stop()

    try:
      loop = asyncio.get_event_loop()
      if loop.is_running():
        self._task = asyncio.create_task(_send())
      else:
        asyncio.run(_send())
    except RuntimeError:
      asyncio.run(_send())

if __name__ == "__main__":
  bot = TelegramBot()
  bot.send_message("Hello, world!")
