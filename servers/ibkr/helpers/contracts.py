"""Contract operations."""
from ib_async import util
from ib_async.contract import Contract, Option
from loguru import logger

from .client import IBClient

class ContractClient(IBClient):
  """Contract operations.

  Available public methods:
    - get_contract_details: get contract details for a given symbol
    - get_options_chain: get options chain for a given underlying contract

  """

  async def get_contract_details(
      self,
      symbol: str,
      sec_type: str,
      exchange: str,
      options: dict | None = None,
    ) -> list[str]:
    """Get contract details for a given symbol.

    Args:
      symbol: Symbol to get contract details for.
      sec_type: Security type to get contract details for, supported types are:
        - STK: Stock
        - IND: Index
        - CASH: Currency
        - BOND: Bond
        - FUT: Future
        - OPT: Option
      exchange: Exchange to get contract details for, supported exchanges are:
        - CBOE: CBOE
        - NYSE: NYSE
        - ARCA: ARCA
        - BATS: BATS
        - NASDAQ: NASDAQ
      options: Dictionary of options to get contract details for.
        - strike: Strike price to get contract details for.
        - right: Right to get contract details for.
        - lastTradeDateOrContractMonth: Last trade date or contract month.
        - tradingClass: Trading class to get contract details for.

    Returns:
        List of contract details for the given symbol.

    """
    try:
      await self._connect()

      contract_params = {
        "strike": 0,
        "right": "",
        "lastTradeDateOrContractMonth": "",
        "tradingClass": "",
        "comboLegs": [],
      }
      if options:
        contract_params.update(options)

      contract = Contract(
        conId=0,
        symbol=symbol,
        exchange=exchange,
        secType=sec_type,
        **contract_params,
      )

      contracts = await self.ib.qualifyContractsAsync(contract)
      contracts = util.df(contracts)
      contracts = contracts[[
        "conId",
        "symbol",
        "secType",
        "exchange",
        "currency",
        "localSymbol",
        "multiplier",
      ]]
    except Exception as e:
      logger.error("Error getting contract details: {}", str(e))
      raise
    else:
      return contracts.to_json(orient="records")

  async def get_options_chain(
    self,
    underlying_symbol: str,
    underlying_sec_type: str,
    underlying_con_id: int,
    filters: dict | None = None,
    ) -> list[str]:
    """Get options chain for a given underlying contract.

    NOTE: skipping exchange filter as conId is the same, using only "SMART"

    Args:
      underlying_symbol: Symbol of the underlying contract.
      underlying_sec_type: Security type of the underlying contract.
      underlying_con_id: ConID of the underlying contract.
      filters: Dictionary of filters to apply to the options chain.
        - tradingClass: List of trading classes to filter by.
        - expirations: List of expirations to filter by.
        - strikes: List of strikes to filter by.
        - rights: List of rights to filter by.


    Returns:
      List of options chain for the given underlying contract.

    """
    try:
      await self._connect()
      chains = await self.ib.reqSecDefOptParamsAsync(
        underlying_symbol,
        "",
        underlying_sec_type,
        underlying_con_id,
      )
      chains = util.df(chains)
      chains = chains[[
        "exchange",
        "underlyingConId",
        "tradingClass",
        "expirations",
        "strikes",
      ]]

      if filters:
        expirations = filters.get("expirations", chains["expirations"].iloc[0])
        strikes = filters.get("strikes", chains["strikes"].iloc[0])
        rights = filters.get("rights", ["C", "P"])
        trading_classes = filters.get("tradingClass", chains["tradingClass"].unique())
      else:
        expirations = chains["expirations"].iloc[0]
        strikes = chains["strikes"].iloc[0]
        rights = ["C", "P"]
        trading_classes = chains["tradingClass"].unique()
      contracts = [
        Option(
          underlying_symbol,
          expiry,
          strike,
          right,
          "SMART",
          tradingClass=trading_class,
        )
        for right in rights
        for strike in strikes
        for expiry in expirations
        for trading_class in trading_classes
      ]

      try:
        contracts = await self.ib.qualifyContractsAsync(*contracts)
        contracts = util.df(contracts)
        contracts = contracts[[
          "conId",
          "localSymbol",
        ]]
      except Exception as e:
        logger.debug("Error qualifying contracts: {}", str(e))
    except Exception as e:
      logger.error("Error getting options chain: {}", str(e))
      raise
    else:
      return contracts.to_json(orient="records")
