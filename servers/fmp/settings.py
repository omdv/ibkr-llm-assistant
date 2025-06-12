"""Settings for the FMP MCP server."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  """Configuration settings for the FMP MCP server."""

  # Server settings
  timeout_seconds: int = 10
  server_timezone: str = "America/New_York"
  quotes_api_key: str
