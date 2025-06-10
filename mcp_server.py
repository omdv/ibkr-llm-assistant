"""MCP Server for IBKR data."""

from loguru import logger
from fastmcp import FastMCP

from src.mcp_servers import ibkr, fmp, calendar

main_mcp = FastMCP(
  name="main_mcp",
  log_level="WARNING",
)

main_mcp.mount("ibkr", ibkr)
main_mcp.mount("fmp", fmp)
main_mcp.mount("calendar", calendar)

if __name__ == "__main__":
  try:
    main_mcp.run(transport="stdio")
  except Exception as e:
    logger.error("MCP server error: {}", str(e))
    raise
