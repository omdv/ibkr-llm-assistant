"""Financial Modeling Prep API events fetcher."""

import httpx
from datetime import datetime
from zoneinfo import ZoneInfo
from loguru import logger
from src.utilities import setup_logging, Settings

setup_logging()

class FMPEventsError(Exception):
  """Custom exception for FMP events errors."""

  def __init__(self, status_code: int) -> None:
    """Initialize the FMPEventsError class."""
    self.status_code = status_code
    super().__init__(f"FMP Events error: {self.status_code}")


class FMPEventsFetcher:
  """Fetches events from Financial Modeling Prep API."""

  def __init__(self) -> None:
    """Initialize the FMPEventsFetcher class."""
    self.settings = Settings()
    self.api_key = self.settings.quotes_api_key
    self.base_url = "https://financialmodelingprep.com/api/v3"
    self.server_tz = ZoneInfo(self.settings.server_timezone)

  def _convert_to_server_timezone(self, date_str: str) -> str:
    """Convert date string to server timezone.

    Args:
        date_str: Date string in format 'YYYY-MM-DD HH:MM:SS'

    Returns:
        str: Date string in server timezone

    """
    try:
      # Parse the input date string and explicitly set as UTC
      utc_dt = datetime.strptime(
        date_str,
        "%Y-%m-%d %H:%M:%S",
      ).replace(tzinfo=ZoneInfo("UTC"))

      # Convert to server timezone
      server_dt = utc_dt.astimezone(self.server_tz)

      # Format back to string
      return server_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
      logger.error(f"Error converting date {date_str}: {str(e)!r}")
      return date_str

  async def get_events(
      self,
      from_date: str,
      to_date: str,
      impact: list[str] | None = None,
      countries: list[str] | None = None,
  ) -> float:
    """Fetch events for a given date range asynchronously.

    Args:
        from_date: Start date of the events
        to_date: End date of the events
        impact: Impact of the events
        countries: Countries of the events

    """
    url = f"{self.base_url}/economic_calendar"
    params = {"from": from_date, "to": to_date, "apikey": self.api_key}

    async with httpx.AsyncClient() as client:
      response = await client.get(
        url,
        params=params,
        timeout=self.settings.timeout_seconds,
      )

      if response.status_code != 200:
        raise FMPEventsError(response.status_code)

      data = response.json()
      if not data:
        raise FMPEventsError(404)

      # Set defaults if not provided
      impact = impact or ["High", "Medium"]
      countries = countries or ["US", "GB", "CN", "EA"]

      # Filter and convert dates in each event to server timezone
      filtered_data = [
        event for event in data
        if event.get("impact") in impact and event.get("country") in countries
      ]

      # Convert dates to server timezone
      for event in filtered_data:
        if "date" in event:
          event["date"] = self._convert_to_server_timezone(event["date"])

      return filtered_data
