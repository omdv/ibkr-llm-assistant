"""Trading-related tools."""
from loguru import logger
import json
from src.mcp_servers.ibkr import ibkr, ib_interface

@ibkr.tool(name="trade_simple_contract")
async def trade_simple_contract(
  con_id: int,
  action: str,
  quantity: int,
  order_type: str,
  price: float | None = None,
) -> str:
  """Trade a simple non-combo contract.

  Args:
    con_id: Contract ID to trade.
    action: Action, supported actions are BUY or SELL
    quantity: Quantity to trade.
    order_type: Order type, supported order types are market (MKT) or limit (LMT)
    price: Price to trade.

  Returns:
    str: A formatted string containing the result of the order or error message

  Example:
    >>> await trade_single_instrument(
    ...     contract=Contract(symbol="AAPL", sec_type="STK", exchange="NASDAQ"),
    ...     order=Order(action="BUY", quantity=100, price=150.75),
    ... )
    "Order executed"

  """
  logger.debug(
    "Tool trade_single_instrument called with parameters: {!s}, {!s}, {!s}, {!s}, {!s}",
    con_id,
    action,
    order_type,
    quantity,
    price,
  )
  try:
    result = await ib_interface.trade_simple_contract(
      con_id=con_id,
      action=action,
      quantity=quantity,
      order_type=order_type,
      price=price,
    )
    logger.debug("Order result: {!s}", result)

    trade_data = json.loads(result) if isinstance(result, str) else result
    if trade_data.get("error"):
      return f"Error executing trade: {trade_data['error']}"

    trade_info = trade_data.get("trade", {})
    contract = trade_info.get("contract", {})
    order = trade_info.get("order", {})
    order_status = trade_info.get("orderStatus", {})
  except Exception as e:
    logger.error("Error in trade_simple_contract: {!s}", str(e))
    return f"Error trading simple contract: {str(e)!s}"
  else:
    return (
      f"Order: {order} for contract: {contract} "
      f"has been executed with status: {order_status}"
    )

@ibkr.tool(name="trade_combo_contract")
async def trade_combo_contract(
  legs: dict[int, str],
  action: str,
  quantity: int,
  order_type: str,
  price: float | None = None,
) -> str:
  """Trade a combo contract.

  Args:
    legs: Dictionary of conIds to trade combo contract for, with action as value.
      Example: {123456: "BUY", 123457: "SELL"}
    action: Action to trade combo contract for, supported actions are:
      - BUY: Buy
      - SELL: Sell
    quantity: Quantity to trade combo contract for.
    order_type: Order type, supported order types are market (MKT) or limit (LMT)
    price: Price to trade combo contract for.

  Returns:
    str: A formatted string containing the result of the order or error message

  Example:
    >>> await open_option_spread(
    ...     con_ids=[123456, 789012],
    ...     ratios=[1, 1],
    ...     actions=["BUY", "SELL"],
    ...     target_price=150.75,
    ... )
    "Order executed"

  """
  logger.debug(
    "Tool trade_combo_contract called with parameters: {!s}, {!s}, {!s}, {!s}, {!s}",
    legs,
    action,
    quantity,
    order_type,
    price,
  )
  try:
    result = await ib_interface.trade_combo_contract(
      legs,
      action,
      quantity,
      order_type,
      price,
    )
    logger.debug("Order result: {!s}", result)

    trade_data = json.loads(result) if isinstance(result, str) else result
    if trade_data.get("error"):
      return f"Error executing trade: {trade_data['error']}"

    trade_info = trade_data.get("trade", {})
    contract = trade_info.get("contract", {})
    order = trade_info.get("order", {})
    order_status = trade_info.get("orderStatus", {})
  except Exception as e:
    logger.error("Error in trade_combo_contract: {!s}", str(e))
    return f"Error trading combo contract: {str(e)!s}"
  else:
    return (
      f"Order: {order} for contract: {contract} "
      f"has been executed with status: {order_status}"
    )
