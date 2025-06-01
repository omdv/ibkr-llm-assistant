"""Settings for the IBKR MCP server."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  """Configuration settings for the IBKR MCP server."""

  # Global settings
  verbose: bool = False
  log_file: str = "logs/app.log"
  mcp_server_script: str = "./mcp_server.py"
  timeout_seconds: int = 10
  server_timezone: str = "America/New_York"
  max_prompt_length: int = 2000
  database_host: str = "localhost"
  database_port: int = 5432
  web_port: int = 8000

  # MCP server settings
  ib_gateway_host: str
  ib_gateway_port: str
  ib_command_server_port: str
  quotes_api_key: str

  # MCP client settings
  anthropic_api_key: str
  chat_model: str = "claude-3-5-sonnet-20241022"
  chat_model_max_tokens: int = 1000

  # Telegram approval bot settings
  telegram_bot_token: str
  telegram_allowed_user_id: str
  telegram_approval_timeout: int = 300
