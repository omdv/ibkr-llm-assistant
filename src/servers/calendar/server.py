"""MCP Calendar server."""

import pytz
import pandas as pd
import exchange_calendars as xcals
from datetime import datetime
from fastmcp import FastMCP
from loguru import logger

from src.servers.calendar.settings import Settings

calendar = FastMCP("calendar")

@calendar.tool(name="current_datetime")
async def get_current_datetime() -> str:
  """Get the current datetime.

  Returns:
    str: The current datetime in the format YYYY-MM-DD HH:MM:SS.

  """
  server_timezone = Settings().server_timezone
  return datetime.now(pytz.timezone(server_timezone)).strftime("%Y-%m-%d %H:%M:%S")

@calendar.tool(name="get_calendar")
async def get_calendar(num_days: int = 5) -> str:
  """Get the calendar for the exchange for the next num_days days.

  Args:
    num_days: The number of days to get the calendar for.

  Returns:
    str: The calendar for the next num_days days in the server timezone.

  """
  num_days = min(num_days, 14)
  server_timezone = Settings().server_timezone
  nyse = xcals.get_calendar("XNYS")
  today = datetime.now(pytz.timezone(server_timezone))

  schedule = nyse.schedule
  schedule = schedule.loc[schedule.index >= today.strftime("%Y-%m-%d")]
  schedule = schedule.loc[
    schedule.index < (today + pd.Timedelta(days=num_days)).strftime("%Y-%m-%d")]

  # Adjust the timestamps to the server timezone
  schedule["open"] = schedule["open"].dt.tz_convert(server_timezone)
  schedule["close"] = schedule["close"].dt.tz_convert(server_timezone)

  # Convert to LLM-readable format
  schedule["open"] = schedule["open"].dt.strftime("%Y-%m-%d %H:%M:%S")
  schedule["close"] = schedule["close"].dt.strftime("%Y-%m-%d %H:%M:%S")

  return schedule.to_json(orient="records")

if __name__ == "__main__":
  try:
    calendar.run(transport="stdio")
  except Exception as e:
    logger.error("MCP server error: {}", str(e))
    raise
