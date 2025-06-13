"""Settings for the IBKR MCP server."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  """Configuration settings for the IBKR MCP server."""

  # Global settings
  server_timezone: str = "America/New_York"
