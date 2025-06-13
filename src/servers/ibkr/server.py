"""Launch the IBKR MCP server."""

from src.servers.ibkr.tools import ibkr

if __name__ == "__main__":
  ibkr.run()
