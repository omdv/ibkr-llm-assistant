"""Contract and options-related tools."""
from loguru import logger
from src.servers.ibkr.tools import ibkr, ib_interface

@ibkr.tool(name="get_contract_details")
async def get_contract_details(
  symbol: str,
  sec_type: str,
  exchange: str,
  options: dict | None = None,
) -> str:
  """Get contract details for a given symbol.

  Args:
    symbol: Symbol to get contract details for.
    sec_type: Security type (STK, IND, CASH, BAG, BOND, FUT, OPT)
    exchange: Exchange (CBOE, NYSE, ARCA, BATS, NASDAQ)
    options: Optional parameters including:
      - lastTradeDateOrContractMonth: Expiry date for options - "YYYYMMDD"
      - strike: Strike price for options
      - right: Right for options - "C" or "P"
      - tradingClass: for weekly options of SPX use SPXW

  Returns:
    str: A formatted string containing the contract details or error message

  Example:
    >>> get_contract_details(
    ...     symbol="AAPL",
    ...     sec_type="STK",
    ...     exchange="NASDAQ",
    ... )
    "The contract details for the symbol are:
      {'symbol': 'AAPL',
      'secType': 'STK',
      'exchange': 'NASDAQ'}"

  """
  try:
    options = options or {}
    details = await ib_interface.get_contract_details(
      symbol=symbol,
      sec_type=sec_type,
      exchange=exchange,
      options=options,
    )
  except Exception as e:
    logger.error("Error in get_contract_details: {!s}", str(e))
    return "Error getting contract details"
  else:
    return f"The contract details for the symbol are: {details}"

@ibkr.tool(name="get_options_chain")
async def get_options_chain(
  underlying_symbol: str,
  underlying_sec_type: str,
  underlying_con_id: int,
  filters: dict | None = None,
) -> str:
  """Get options chain for a given underlying contract.

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

  Returns:
    str: A formatted string containing the options chain or error message

  Example:
    >>> get_options_chain(
    ...     underlying_symbol="SPX",
    ...     underlying_sec_type="IND",
    ...     underlying_con_id=416904,
    ...     filters={
    ...       "tradingClass": ["SPXW"],
    ...       "expirations": ["20250505"],
    ...       "strikes": [5490],
    ...       "rights": ["C", "P"],
    ...     },
    ... )
    "The options chain for the underlying contract is: [
      [
      {"conId":771890640,"localSymbol":"SPXW  250505P06200000"},
      {"conId":771890645,"localSymbol":"SPXW  250505P06400000"},
      {"conId":771890655,"localSymbol":"SPXW  250505P06600000"},
      {"conId":771890665,"localSymbol":"SPXW  250505P06800000"},
      {"conId":771890685,"localSymbol":"SPXW  250505P07000000"},
      {"conId":771890699,"localSymbol":"SPXW  250505P07200000"},
      {"conId":771890709,"localSymbol":"SPXW  250505P07400000"},
    ]"

  """
  try:
    options_chain = await ib_interface.get_options_chain(
      underlying_symbol,
      underlying_sec_type,
      underlying_con_id,
      filters,
    )
  except Exception as e:
    logger.error("Error in get_options_chain: {!s}", str(e))
    return "Error getting options chain"
  else:
    return f"The options chain for the underlying contract is: {options_chain}"

@ibkr.tool(name="get_tickers")
async def get_tickers(contract_ids: list[int]) -> str:
  """Get tickers for a list of contract IDs.

  This function queries the IB TWS to get the tickers for a list of contract IDs.
  It will return the last price and symbol, and greeks (if applicable).

  Args:
    contract_ids (list[int]): A list of contract IDs to get tickers for.

  Returns:
    str: A formatted string containing the tickers for the contract IDs.

  Example:
      >>> await get_tickers_details([123456, 789012])
      "The tickers details for the contract IDs are: [
        {'symbol': 'AAPL', 'last_price': 150.75, 'greeks': {},
        {'symbol': 'MSFT', 'last_price': 210.22, 'greeks': {}},
      ]"

  """
  try:
    tickers = await ib_interface.get_tickers(contract_ids)
  except Exception as e:
    logger.error("Error in get_tickers: {!s}", str(e))
    return "Error getting tickers"
  else:
    return f"The tickers for the contract IDs are: {tickers}"

@ibkr.tool(name="get_and_filter_options_chain")
async def get_and_filter_options_chain(
  underlying_symbol: str,
  underlying_sec_type: str,
  underlying_con_id: int,
  filters: dict | None = None,
  criteria: dict | None = None,
) -> str:
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
    criteria: Dictionary of criteria to filter by.
      - min_delta: Minimum delta value (float)
      - max_delta: Maximum delta value (float)

  Returns:
    str: A formatted string containing the filtered options.

  Example:
    >>> await get_and_filter_options(
    ...     underlying_symbol="SPX",
    ...     underlying_sec_type="IND",
    ...     underlying_con_id=416904,
    ...     filters={
    ...       "tradingClass": ["SPXW"],
    ...       "expirations": ["20250505"],
    ...       "strikes": [5490],
    ...       "rights": ["C", "P"],
    ...     },
    ...     criteria={"min_delta": -0.06, "max_delta": -0.04},
    ... )
    "The filtered options for the contract IDs are: [
      {'symbol': 'AAPL', 'last_price': 150.75, 'greeks': {}},
    ]"

  """
  try:
    filtered_options = await ib_interface.get_and_filter_options(
      underlying_symbol,
      underlying_sec_type,
      underlying_con_id,
      filters,
      criteria,
    )
  except Exception as e:
    logger.error("Error in filter_options: {!s}", str(e))
    return "Error filtering options"
  else:
    return f"The filtered options for the contract IDs are: {filtered_options}"
