"""Market data operations."""
import asyncio
import pandas as pd
import exchange_calendars as ecals
import datetime as dt
from loguru import logger
from ib_async import util
from ib_async.contract import Contract

from .client import IBClient
from .contracts import ContractClient

class MarketDataClient(IBClient):
  """Market data operations."""

  def __init__(self) -> None:
    """Initialize the MarketDataClient."""
    super().__init__()
    self.contract_client = ContractClient()
    self.contract_client.ib = self.ib

  def _is_market_open(self) -> bool:
      """Check if the market is open."""
      nyse = ecals.get_calendar("NYSE")
      return nyse.is_trading_minute(dt.datetime.now(dt.UTC))

  async def get_tickers(
      self,
      contract_ids: list[int],
    ) -> list[str]:
    """Get tickers for a list of contract IDs.

    Args:
        contract_ids: List of contract IDs to get tickers for.

    Returns:
        List of tickers for the given contract IDs.

    """
    try:
      await self._connect()
      contracts = [Contract(conId=contract_id) for contract_id in contract_ids]
      qualified_contracts = await self.ib.qualifyContractsAsync(*contracts)

      # First attempt to get tickers
      if self._is_market_open():
        logger.debug("Market is open, requesting live market data")
        self.ib.reqMarketDataType(1)
      else:
        logger.debug("Market is closed, requesting delayed market data")
        self.ib.reqMarketDataType(2)
      tickers = await self.ib.reqTickersAsync(*qualified_contracts)

      # Process tickers
      result = util.df(tickers)
      result["contractId"] = result["contract"].apply(lambda x: x.conId)
      result["symbol"] = result["contract"].apply(lambda x: x.localSymbol)
      result["last"] = result["last"].astype(float)
      result["bid"] = result["bid"].astype(float)
      result["ask"] = result["ask"].astype(float)

      def greek_extraction(ticker: pd.Series) -> dict | None:
        greeks_data = {}
        if hasattr(ticker, "modelGreeks") and ticker.modelGreeks:
          greeks_data["model"] = {
            "delta": ticker.modelGreeks.delta,
            "gamma": ticker.modelGreeks.gamma,
            "vega": ticker.modelGreeks.vega,
            "theta": ticker.modelGreeks.theta,
            "impliedVol": ticker.modelGreeks.impliedVol,
          }
        return greeks_data

      result["greeks"] = result.apply(greek_extraction, axis=1)

      # Check if we got any greeks data
      has_greeks = any(result["greeks"].apply(lambda x: bool(x)))

      if not has_greeks:
        logger.warning("No greeks data received, restarting gateway...")
        await self.send_command_to_ibc("RESTART")
        await asyncio.sleep(30)
        await self._connect()

        # Second attempt
        if self._is_market_open():
          self.ib.reqMarketDataType(1)
        else:
          self.ib.reqMarketDataType(2)
        tickers = await self.ib.reqTickersAsync(*qualified_contracts)

        # Process tickers again
        result = util.df(tickers)
        result["contractId"] = result["contract"].apply(lambda x: x.conId)
        result["symbol"] = result["contract"].apply(lambda x: x.localSymbol)
        result["last"] = result["last"].astype(float)
        result["bid"] = result["bid"].astype(float)
        result["ask"] = result["ask"].astype(float)
        result["greeks"] = result.apply(greek_extraction, axis=1)

        # Check if we got greeks data after restart
        has_greeks = any(result["greeks"].apply(lambda x: bool(x)))
        if not has_greeks:
          logger.warning("Still no greeks data after gateway restart")

      result = result[[
        "contractId",
        "symbol",
        "last",
        "bid",
        "ask",
        "greeks",
      ]]

    except Exception as e:
      logger.error("Error getting tickers: {}", str(e))
      raise
    else:
      return result.to_json(orient="records")

  async def get_and_filter_options(
      self,
      underlying_symbol: str,
      underlying_sec_type: str,
      underlying_con_id: int,
      filters: dict | None = None,
      criteria: dict | None = None,
    ) -> list[dict]:
    """Get and filter option chain based on market data criteria.

    Args:
      underlying_symbol: Symbol of the underlying contract.
      underlying_sec_type: Security type of the underlying contract.
      underlying_con_id: ConID of the underlying contract.
      filters: Dictionary of filters to apply to the options chain,
      you must specify at least one filter to reduce the number of options in the chain,
      you must specify expirations, you can specify tradingClass, strikes, and rights.
        - tradingClass: List of trading classes to filter by.
        - expirations: List of expirations to filter by.
        - strikes: List of strikes to filter by.
        - rights: List of rights to filter by.
      criteria: Dictionary of criteria to match:
        - min_delta: Minimum delta value (float)
        - max_delta: Maximum delta value (float)

    Returns:
      List of dictionaries containing filtered option details and market data

    """
    try:
      await self._connect()  # Connect once for both operations

      # Get options chain
      options_chain_json = await self.contract_client.get_options_chain(
        underlying_symbol,
        underlying_sec_type,
        underlying_con_id,
        filters,
      )
      options_chain = pd.read_json(options_chain_json)

      # Get market data for all options
      market_data_json = await self.get_tickers(options_chain["conId"].tolist())
      market_data = pd.read_json(market_data_json)

      if market_data.empty:
        logger.warning("No market data available for options")
        return []

      # Apply criteria filters
      filtered_data = market_data.copy()

      # Apply delta range if specified
      if criteria and ("min_delta" in criteria or "max_delta" in criteria):
        # Filter out rows with missing greeks data first
        filtered_data = filtered_data[
          filtered_data["greeks"].apply(
            lambda x: bool(x and "model" in x and x["model"].get("delta") is not None),
          )
        ]

        # Apply delta filters
        filtered_data = filtered_data[
          filtered_data["greeks"].apply(
            lambda x: (
              ("min_delta" not in criteria or
                x["model"]["delta"] >= criteria["min_delta"]) and
              ("max_delta" not in criteria or
                x["model"]["delta"] <= criteria["max_delta"])
            ),
          )
        ]

      if filtered_data.empty:
        logger.warning("No options found matching the criteria")
        return []

      # Return all matching options
      return filtered_data.to_dict(orient="records")

    except Exception as e:
      logger.error("Error filtering options: {}", str(e))
      raise
