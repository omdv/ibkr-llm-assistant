"""Settings for the MCP client."""
from pydantic_settings import BaseSettings

class MySettings(BaseSettings):
  """Configuration settings for the MCP client."""

  # application settings
  database_host: str = "localhost"
  database_port: int = 5432
  web_port: int = 3000

  # MCP server settings
  server_timezone: str = "America/New_York"
  ib_gateway_host: str
  ib_gateway_port: str
  ib_command_server_port: str
  quotes_api_key: str
  telegram_bot_token: str
  telegram_allowed_user_id: str
  telegram_approval_timeout: int=300

  # MCP agent settings
  anthropic_api_key: str
  anthropic_model: str = "claude-3-5-sonnet-20240620"
  anthropic_model_max_tokens: int = 2000
