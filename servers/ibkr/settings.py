"""Settings for the IBKR MCP server."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  """Configuration settings for the IBKR MCP server."""

  # Server settings
  ib_gateway_host: str
  ib_gateway_port: str
  ib_command_server_port: str
  telegram_bot_token: str
  telegram_allowed_user_id: str
  telegram_approval_timeout: int = 300
