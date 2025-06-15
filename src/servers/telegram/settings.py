"""Settings for the IBKR MCP server."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  """Configuration settings for the IBKR MCP server."""

  # Server settings
  telegram_bot_token: str
  telegram_allowed_user_id: str
