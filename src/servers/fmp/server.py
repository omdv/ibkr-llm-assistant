"""MCP server setup."""

import json
from fastmcp import FastMCP
from loguru import logger

from src.servers.fmp.helpers import FMPQuoteFetcher, FMPEventsFetcher

# Initialize server
fmp = FastMCP("fmp")

# Initialize shared interfaces
fmp_quotes = FMPQuoteFetcher()
fmp_events = FMPEventsFetcher()

@fmp.tool(name="get_stock_quote")
async def get_stock_quote(symbol: str) -> str:
  """Get quote for a stock symbol.

  Args:
    symbol (str): The stock symbol to get the quote for.

  Returns:
    str: A formatted string containing the quote for the stock symbol.
    Index symbols should be prefixed with "^"

  Example:
      >>> get_stock_quote("AAPL")
      "The current price of AAPL is 150.75."
      >>> get_stock_quote("^SPX")
      "The current price of ^SPX is 4500.00."

  """
  try:
    quote = await fmp_quotes.get_spot_quote(symbol, "price")
    result = f"The current price of {symbol} is {quote}."
  except Exception as e:
    logger.error("Error in get_quote: {!s}", str(e))
    return "Error getting quote"
  else:
    return result


@fmp.tool(name="get_stock_quotes_batch")
async def get_stock_quotes_batch(symbols: list[str]) -> str:
  """Get quotes for a list of stock symbols.

  Args:
    symbols (list[str]): A list of stock symbols to get quotes for.

  Returns:
    str: A formatted string containing the quotes for the stock symbols.

  Example:
      >>> get_stock_quotes_batch(["AAPL", "MSFT"])
      "Current Stock Quotes: {'AAPL': 150.75, 'MSFT': 210.22}"

  """
  try:
    quotes = await fmp_quotes.get_batch_quotes(symbols)
    # Create a formatted table string
    response = f"Current Stock Quotes: {quotes}"
  except Exception as e:
    logger.error("Error in get_stock_quotes_batch: {!s}", str(e))
    return "Error getting stock quotes"
  else:
    return response


@fmp.tool(name="get_events")
async def get_events(from_date: str, to_date: str) -> str:
  """Get economic events for a given date range in the server's timezone.
  You need to specify filters for impact and countries otherwise you will get overloaded.

  Args:
    from_date (str): The start date of the calendar.
    to_date (str): The end date of the calendar.
    impact (list[str]): The impact of the events, "High", "Medium", "Low"
    countries (list[str]): The countries of the events, two letter ISO codes

  Returns:
    str: JSON string containing the events for given date range in server's timezone.

  Example:
      >>> get_events("2025-06-09", "2025-06-10")
      '[{"date": "2025-06-09", "event": "CPI", "impact": "High", "country": "US"}]'
      >>> get_events("2025-06-09", "2025-06-10", impact=["High"], countries=["US"])
      '[{"date": "2025-06-09", "event": "CPI", "impact": "High", "country": "US"}]'

  """
  try:
    events = await fmp_events.get_events(from_date, to_date)
    result = json.dumps(events)
  except Exception as e:
    logger.error("Error in get_events: {!s}", str(e))
    return "Error getting events"
  else:
    return result

if __name__ == "__main__":
  try:
    fmp.run(transport="stdio")
  except Exception as e:
    logger.error("MCP server error: {}", str(e))
    raise
