"""Financial Modeling Prep API spot quote fetcher."""

import json
import httpx
from loguru import logger

from src.utilities import setup_logging, Settings

setup_logging()

class FMPQuoteError(Exception):
  """Custom exception for FMP quote errors."""

  def __init__(self, status_code: int) -> None:
    """Initialize the FMPQuoteError class."""
    self.status_code = status_code
    super().__init__(f"FMP API error: {self.status_code}")


class FMPQuoteFetcher:
  """Fetches spot quotes from Financial Modeling Prep API."""

  def __init__(self) -> None:
    """Initialize the FMPQuoteFetcher class."""
    self.settings = Settings()
    self.api_key = self.settings.quotes_api_key
    self.base_url = "https://financialmodelingprep.com/api/v3"

  async def get_spot_quote(self, symbol: str, price_type: str) -> float:
    """Fetch spot quote for symbol asynchronously.

    Args:
        symbol: Stock symbol
        price_type: Type of price to return (e.g. 'price', 'open', 'high', 'low', etc)

    """
    url = f"{self.base_url}/quote/{symbol}"
    params = {"apikey": self.api_key}

    async with httpx.AsyncClient() as client:
      response = await client.get(
        url,
        params=params,
        timeout=self.settings.timeout_seconds,
      )

      if response.status_code != 200:
        raise FMPQuoteError(response.status_code)

      data = response.json()
      if not data:
        raise FMPQuoteError(404)

      return float(data[0][price_type])

  async def get_batch_quotes(self, symbols: list[str]) -> str:
    """Get batch quotes for a list of symbols."""
    quotes = {}
    for symbol in symbols:
      try:
        quote = await self.get_spot_quote(symbol, "price")
        quotes[symbol] = quote
      except Exception as e:
        logger.error("Error getting quote for {}: {}", symbol, str(e))
        quotes[symbol] = None
    return json.dumps({k: v for k, v in quotes.items() if v is not None})
