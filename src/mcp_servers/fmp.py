"""MCP server setup."""
from loguru import logger
from fastmcp import FastMCP
import json

from src.utilities import setup_logging
from src.fmp_helpers.fmp_quotes_helper import FMPQuoteFetcher
from src.fmp_helpers.fmp_events_helper import FMPEventsFetcher

setup_logging()

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
      >>> await get_stock_quote("AAPL")
      "The current price of AAPL is 150.75."
      >>> await get_stock_quote("^SPX")
      "The current price of ^SPX is 4500.00."

  """
  logger.debug("Tool get_stock_quote called with symbol: {!s}", symbol)
  try:
    quote = await fmp_quotes.get_spot_quote(symbol, "price")
    result = f"The current price of {symbol} is {quote}."
    logger.debug("get_quote result: {!s}", result)
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
      >>> await get_stock_quotes_batch(["AAPL", "MSFT"])
      "Current Stock Quotes: {'AAPL': 150.75, 'MSFT': 210.22}"

  """
  logger.debug("Tool get_stock_quotes_batch called with symbols: {!s}", symbols)
  try:
    quotes = await fmp_quotes.get_batch_quotes(symbols)
    # Create a formatted table string
    response = f"Current Stock Quotes: {quotes}"
    logger.debug("get_stock_quotes_batch result: {!s}", response)
  except Exception as e:
    logger.error("Error in get_stock_quotes_batch: {!s}", str(e))
    return "Error getting stock quotes"
  else:
    return response


@fmp.tool(name="get_events")
async def get_events(from_date: str, to_date: str) -> str:
  """Get economic events for a given date range in the server's timezone.

  Args:
    from_date (str): The start date of the calendar.
    to_date (str): The end date of the calendar.
    impact (list[str]): The impact of the events, "High", "Medium", "Low"
    countries (list[str]): The countries of the events, two letter ISO codes

  Returns:
    str: JSON string containing the events for given date range in server's timezone.

  Example:
      >>> await get_events("2025-06-09", "2025-06-10")
      '[{"date": "2025-06-09", "event": "CPI", "impact": "High", "country": "US"}]'
      >>> await get_events("2025-06-09", "2025-06-10", impact=["High"], countries=["US"])
      '[{"date": "2025-06-09", "event": "CPI", "impact": "High", "country": "US"}]'

  """
  logger.debug(
    "Tool get_events called with from_date: {!s} and to_date: {!s}",
    from_date,
    to_date,
  )
  try:
    events = await fmp_events.get_events(from_date, to_date)
    result = json.dumps(events)
    logger.debug("get_events result: {!s}", result)
  except Exception as e:
    logger.error("Error in get_events: {!s}", str(e))
    return "Error getting events"
  else:
    return result
