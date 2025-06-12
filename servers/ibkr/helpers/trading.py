"""Trading operations."""
import asyncio
import json
from loguru import logger
from ib_async.contract import Contract, ComboLeg
from ib_async.order import Order

from .client import IBClient
from servers.ibkr.utilities import TelegramApprovalBot

class TradingClient(IBClient):
  """Trading operations.

  Public methods:
    - trade_simple_contract: Trade a simple non-combo contract.
    - trade_combo_contract: Trade a combo contract.
  """

  def __init__(self) -> None:
    """Initialize OrderClient."""
    super().__init__()
    self.notification_bot = TelegramApprovalBot()
    self._bot_started = False

  async def _ensure_bot_running(self) -> None:
    """Ensure the notification bot is running."""
    if not self._bot_started:
      await self.notification_bot.start()
      self._bot_started = True

  async def _serialize_contract(self, contract: Contract) -> dict:
    """Serialize a Contract object into a dictionary.

    Args:
      contract: Contract object to serialize.

    Returns:
      Dictionary containing relevant contract information.

    """
    base_info = {
      "conId": contract.conId,
      "symbol": contract.symbol,
      "secType": contract.secType,
      "exchange": contract.exchange,
      "currency": contract.currency,
    }

    if contract.secType == "BAG" and contract.comboLegs:
      base_info["legs"] = []
      for leg in contract.comboLegs:
        leg_contract = Contract(conId=leg.conId)
        await self.ib.qualifyContractsAsync(leg_contract)
        base_info["legs"].append({
          "conId": leg_contract.conId,
          "symbol": leg_contract.localSymbol.replace(" ", ""),
          "action": leg.action,
          "ratio": leg.ratio,
        })

    return base_info

  async def _execute_order(
    self,
    contract: Contract,
    action: str,
    quantity: int,
    order_type: str,
    price: float | None = None,
  ) -> str:
    """Place an order and wait for confirmation.

    Args:
      contract: Contract object to place order for.
      action: Action to place order for, supported actions are:
        - BUY: Buy
        - SELL: Sell
      quantity: Quantity to place order for.
      order_type: Order type to place order for, supported order types:
        - market (MKT)
        - limit (LMT)
      price: Desired price to place order for.

    Returns:
      JSON string containing trade information or error message.

    """
    timeout = 10
    order_type = order_type.upper()

    try:
      # Create the order
      order = Order(
        action=action,
        totalQuantity=quantity,
        orderType=order_type,
      )
      if order_type == "LMT":
        order.lmtPrice = price

      # Request approval
      await self._ensure_bot_running()
      logger.debug("Requesting approval for order: {}", contract)

      approved = await self.notification_bot.request_approval(
        message={
          "contract": await self._serialize_contract(contract),
          "order": {
            "action": order.action,
            "totalQuantity": order.totalQuantity,
            "orderType": order.orderType,
            "lmtPrice": order.lmtPrice,
          },
        },
      )

      if not approved:
        logger.debug("Order not approved, skipping")
        return json.dumps({
          "trade": None,
          "error": "Order not approved",
        })

      # Place the order
      logger.debug("Placing order: {}", order)
      trade = self.ib.placeOrder(contract, order)
      logger.debug("Order placed: {}", trade)
      filled = False

      while timeout > 0 and not filled:
        status = trade.orderStatus.status
        if status == "Filled":
          logger.debug("Order filled at {}", trade.orderStatus.avgFillPrice)
          successful_trade = json.dumps({
            "trade": {
              "contract": await self._serialize_contract(trade.contract),
              "order": {
                "orderId": trade.order.orderId,
                "action": trade.order.action,
                "totalQuantity": trade.order.totalQuantity,
                "orderType": trade.order.orderType,
                "lmtPrice": trade.order.lmtPrice,
              },
              "orderStatus": {
                "status": trade.orderStatus.status,
                "filled": trade.orderStatus.filled,
                "remaining": trade.orderStatus.remaining,
                "avgFillPrice": trade.orderStatus.avgFillPrice,
              },
            },
            "error": None,
          })
          await self.notification_bot.send_trade_confirmation(successful_trade)
          return successful_trade
        if status in ["Cancelled", "Error", "Inactive"]:
          logger.debug("{} with status {}", trade.orderStatus.orderId, status)
          return json.dumps({
            "trade": None,
            "error": f"Order {status.lower()}",
          })

        await asyncio.sleep(1)
        timeout -= 1

      if not filled:
        logger.debug("{} not filled, cancelling", trade.order)
        self.ib.cancelOrder(trade.order)
        return json.dumps({
          "trade": None,
          "error": "Order not filled",
        })
    except Exception as e:
      logger.error("Error placing order: {}", str(e))
      return json.dumps({
        "trade": None,
        "error": str(e),
      })

  async def _create_combo_contract(
    self,
    con_ids: list[int],
    actions: list[str],
    exchange: str = "SMART",
  ) -> Contract:
    """Create combo contract from given contracts, ratios, and actions.

    Args:
      con_ids: List of conIds to create combo contract for.
      actions: List of actions to create combo contract for, supported actions are:
        - BUY: Buy
        - SELL: Sell
      exchange: Exchange to create combo contract for, supported exchanges are:
        - SMART: Smart
        - CBOE: CBOE
        - NYSE: NYSE
        - ARCA: ARCA
        - BATS: BATS

    Returns:
      Combo contract for the given contracts, ratios, and actions.

    """
    try:
      await self._connect()

      # Qualify the leg contracts
      leg_contracts = [Contract(conId=con_id) for con_id in con_ids]
      await self.ib.qualifyContractsAsync(*leg_contracts)
      logger.debug("Leg contracts qualified: {}", leg_contracts)

      # Create the combo contract
      combo_contract = Contract(
        conId=0,
        symbol=leg_contracts[0].symbol,
        secType="BAG",
        currency="USD",
        exchange="SMART",
      )
      combo_contract.comboLegs = [
        ComboLeg(
          conId=con_id,
          ratio=1,
          action=action,
          exchange=exchange,
        ) for con_id, action in zip(con_ids, actions, strict=True)
      ]
      logger.debug("Combo contract: {}", combo_contract)

    except Exception as e:
      logger.error("Error creating combo leg: {}", str(e))
      raise
    else:
      return combo_contract

  async def trade_combo_contract(
    self,
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
      order_type: Order type to trade combo contract for, supported order types:
        - market (MKT)
        - limit (LMT)
      price: Price to trade combo contract for.

    Returns:
      JSON string containing trade information or error message.

    """
    try:
      # Create the combo contract
      con_ids = []
      actions = []
      for con_id, leg_action in legs.items():
        con_ids.append(con_id)
        actions.append(leg_action)
      contract = await self._create_combo_contract(con_ids, actions)

      # Open the order
      logger.debug("Placing order for combo contract: {}", contract)
      result = await self._execute_order(
        contract,
        action,
        quantity,
        order_type,
        price,
      )
    except Exception as e:
      logger.error("Error trading combo contract: {}", str(e))
      return json.dumps({
        "trade": None,
        "error": str(e),
      })
    else:
      return result

  async def trade_simple_contract(
    self,
    con_id: int,
    action: str,
    quantity: int,
    order_type: str,
    price: float | None = None,
  ) -> str:
    """Trade a simple non-combo contract.

    Args:
      con_id: Contract ID to trade.
      action: Action to trade, supported actions are:
        - BUY: Buy
        - SELL: Sell
      quantity: Quantity to trade.
      order_type: Order type to trade, supported order types:
        - market (MKT)
        - limit (LMT)
      price: Price to trade.

    Returns:
      JSON string containing trade information or error message.

    """
    try:
      # Create the order
      contract = Contract(conId=con_id)
      await self.ib.qualifyContractsAsync(contract)
      logger.debug("Placing order for contract: {}", contract)
      result = await self._execute_order(
        contract,
        action,
        quantity,
        order_type,
        price,
      )
    except Exception as e:
      logger.error("Error trading simple contract: {}", str(e))
      return json.dumps({
        "trade": None,
        "error": str(e),
      })
    else:
      return result
