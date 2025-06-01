
"""MCP server setup."""
from loguru import logger
from fastmcp import FastMCP

from src.utilities import setup_logging
from src.quote_helpers.fmp_quotes_helper import FMPQuoteFetcher
from src.quote_helpers.yahoo_quotes_helper import YahooQuoteFetcher

setup_logging()

quotes = FastMCP("quotes")

# Initialize shared interfaces
fmp_quotes = FMPQuoteFetcher()
yahoo_quotes = YahooQuoteFetcher()

@quotes.tool(name="get_stock_quote")
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


@quotes.tool(name="get_stock_quotes_batch")
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


@quotes.tool(name="get_options_quote")
async def get_options_quote(symbol: str) -> str:
  """Get options quote for an options symbol by parsing Yahoo Finance page.

  Args:
    symbol (str): The options symbol to get the quote for.

  Returns:
    str: A formatted string containing the quote for the options symbol.

  Example:
      >>> await get_options_quote("SPXW250421P05050000")
      "The current price of SPXW250421P05050000 is 150.75."

  """
  logger.debug("Tool get_options_quote called with symbol: {!s}", symbol)
  try:
    quote = await yahoo_quotes.get_options_quote(symbol)
    result = f"The current price of {symbol} is {quote}."
    logger.debug("get_options_quote result: {!s}", result)
  except Exception as e:
    logger.error("Error in get_options_quote: {!s}", str(e))
    return "Error getting options quote"
  else:
    return result
