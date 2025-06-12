"""Position-related tools."""
from loguru import logger
from servers.ibkr.tools import ibkr, ib_interface

@ibkr.tool(name="get_positions")
async def get_positions() -> str:
  """Get positions for all accounts.

  Returns:
    str: A formatted string containing the positions for the accounts.

  Example:
    >>> await get_positions()
    "Current Positions: {'AAPL': 100, 'MSFT': 200}"

  """
  try:
    data = await ib_interface.get_positions()
    response = f"Current Positions: {data}"
  except Exception as e:
    logger.error("Error in get_positions: {!s}", str(e))
    return "Error getting positions"
  else:
    return response
