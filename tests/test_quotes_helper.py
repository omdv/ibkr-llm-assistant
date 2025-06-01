"""Tests for quotes_helper module."""
import pytest
from unittest.mock import AsyncMock, patch
from src.quote_helpers.fmp_quotes_helper import FMPQuoteFetcher
from src.utilities.settings import Settings


@pytest.fixture
def mock_settings() -> Settings:
  """Create mock settings."""
  return Settings()


@pytest.fixture
def quote_fetcher(mock_settings: Settings) -> FMPQuoteFetcher:
  """Create FMPQuoteFetcher instance with mock settings."""
  with patch("src.quote_helpers.fmp_quotes_helper.Settings", return_value=mock_settings):
      return FMPQuoteFetcher()


@pytest.mark.asyncio
async def test_get_spot_quote_success(quote_fetcher: FMPQuoteFetcher) -> None:
  """Test successful spot quote retrieval."""
  mock_response = AsyncMock()
  mock_response.status_code = 200
  mock_response.json = lambda: [{"price": 150.25}]

  async_client = AsyncMock()
  async_client.__aenter__.return_value.get.return_value = mock_response

  with patch("httpx.AsyncClient", return_value=async_client):
    price = await quote_fetcher.get_spot_quote("AAPL", price_type="price")
    assert price == 150.25


@pytest.mark.asyncio
async def test_get_spot_quote_returns_float(quote_fetcher: FMPQuoteFetcher) -> None:
  """Test that spot quote returns a non-null float value using real API."""
  price = await quote_fetcher.get_spot_quote("TSLA", price_type="price")
  assert isinstance(price, float)
  assert price is not None
  assert price > 0
