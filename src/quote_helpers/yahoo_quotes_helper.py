"""Yahoo Finance options quote fetcher."""

import httpx
from loguru import logger
from bs4 import BeautifulSoup
from src.utilities import setup_logging, Settings

setup_logging()

class YahooQuoteFetcher:
  """Fetches options quotes from Yahoo Finance."""

  def __init__(self) -> None:
    """Initialize the YahooQuoteFetcher class."""
    self.settings = Settings()
    self.base_url = "https://finance.yahoo.com/quote/"

  async def get_options_quote(self, symbol: str) -> float:
    """Very hacky way to get options quote."""
    try:
      url = f"{self.base_url}/{symbol}/"
      headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
      }

      async with httpx.AsyncClient() as session:
        response = await session.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        price_elements = soup.findAll("span", attrs={"data-testid": "qsp-price"})
        if price_elements:
          price_text = price_elements[0].get_text().strip()
          try:
            return float(price_text)
          except ValueError:
            logger.error("Could not convert price text to float: {}", price_text)
            return None
        else:
          logger.error("Price element not found within main content")
          return None

    except Exception as e:
        logger.error("Error in get_options_quote: {}", str(e))
        return f"Error getting options quote: {str(e)!s}"
