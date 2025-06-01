"""Telegram bot for trade approvals."""

import json
import asyncio
from loguru import logger
from uuid import UUID, uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
  Application,
  CallbackQueryHandler,
  ContextTypes,
  CommandHandler,
)
from src.utilities import Settings, setup_logging

setup_logging()

class TelegramApprovalBot:
  """Telegram bot for handling trade approvals."""

  def __init__(self) -> None:
    """Initialize the bot."""
    self.settings = Settings()
    self.token = self.settings.telegram_bot_token
    self.timeout = self.settings.telegram_approval_timeout
    self.chat_id = self.settings.telegram_allowed_user_id
    self.approval_events: dict[UUID, asyncio.Event] = {}
    self.approval_results: dict[UUID, bool] = {}

    # Initialize bot
    self.app = Application.builder().token(self.token).build()

    # Add handlers
    self.app.add_handler(CommandHandler("start", self._start_command))
    self.app.add_handler(CallbackQueryHandler(self._button_callback))

  async def start(self) -> None:
    """Start the bot properly."""
    await self.app.initialize()
    await self.app.start()
    await self.app.updater.start_polling(allowed_updates=["callback_query", "message"])

  async def _start_command(
    self,
    update: Update,
  ) -> None:
    """Handle the /start command."""
    await update.message.reply_text("Trade approval bot is running!")

  async def _button_callback(
    self,
    update: Update,
    _: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Handle button callbacks."""
    if not update or not update.callback_query:
      logger.error("No callback query in update")
      return

    query = update.callback_query
    user_id = str(query.from_user.id)
    allowed_user_id = self.settings.telegram_allowed_user_id

    if user_id != allowed_user_id:
      logger.warning("Unauthorized user {} attempted to approve trade", user_id)
      await query.answer("You are not authorized to approve trades.")
      return

    try:
      data = json.loads(query.data)
      prefix = data["id"]

      matching_orders = [
        order_id for order_id in self.approval_events
        if str(order_id).startswith(prefix)
      ]

      if not matching_orders:
        logger.error("No matching order found for prefix {}", prefix)
        await query.answer("Error: Order not found")
        return

      order_id = matching_orders[0]
      approved = data["a"]
      logger.debug(
        "Trade {} for order {}",
        "approved" if approved else "rejected",
        order_id,
      )

      # Store result and set event
      self.approval_results[order_id] = approved
      if order_id in self.approval_events:
        self.approval_events[order_id].set()

      # Update message
      status = "approved" if approved else "rejected"
      await query.edit_message_text(
        text=f"{query.message.text}\n\nStatus: {status}",
        reply_markup=None,
      )
      await query.answer("Trade " + status)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
      logger.error("Error processing callback: {}", str(e))
      await query.answer("Error processing request")

  async def request_approval(
    self,
    message: dict,
  ) -> bool:
    """Request approval for an order."""
    order_id = uuid4()
    self.approval_events[order_id] = asyncio.Event()

    # Format message
    order_type = message["order"]["orderType"]
    price_str = (
      f" at ${message['order']['lmtPrice']:.2f}"
      if order_type == "LMT"
      else ""
    )

    message_text = (
      "🔔 *Trade Approval Request*\n\n"
      f"Contract:\n```\n{json.dumps(message['contract'], indent=2)}\n```\n\n"
      f"Order:\n```\n"
      f"Action: {message['order']['action']}\n"
      f"Quantity: {message['order']['totalQuantity']}\n"
      f"Type: {order_type}{price_str}\n"
      f"```"
    )

    # Create inline keyboard with properly serialized UUID
    keyboard = [
      [
        InlineKeyboardButton(
          "✅ Approve",
          callback_data=json.dumps({
            "id": str(order_id)[:8],
            "a": True,
          }),
        ),
        InlineKeyboardButton(
          "❌ Reject",
          callback_data=json.dumps({
            "id": str(order_id)[:8],
            "a": False,
          }),
        ),
      ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
      # Send message
      await self.app.bot.send_message(
        chat_id=self.chat_id,
        text=message_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
      )

      # Wait for response or timeout
      try:
        await asyncio.wait_for(
          self.approval_events[order_id].wait(),
          timeout=self.timeout,
        )
        result = self.approval_results.get(order_id, False)
      except TimeoutError:
        result = False
        logger.warning("Approval request timed out for order {}", order_id)

      # Clean up
      self.approval_events.pop(order_id, None)
      self.approval_results.pop(order_id, None)

    except Exception as e:
      logger.error("Error requesting approval: {}", str(e))
      return False
    else:
      return result

  async def send_trade_confirmation(
    self,
    trade_message: str,
  ) -> None:
    """Send a trade confirmation message to the user.

    Args:
      trade_message: JSON string containing trade information

    Example:
      {
        "trade": {
          "contract": {
            "symbol": "AAPL",
            "legs": [{"action": "BUY", "ratio": 1, "symbol": "AAPL"}]
          },
          "order": {
            "orderId": 1234567890,
            "action": "BUY",
            "totalQuantity": 100,
            "orderType": "LMT",
            "lmtPrice": 100.00
          },
          "orderStatus": {
            "status": "FILLED",
            "filled": 100,
            "remaining": 0,
            "avgFillPrice": 100.00
          }
        },
        "error": None
      }

    """
    try:
      trade_data = json.loads(trade_message)
      trade = trade_data.get("trade", {})
      contract = trade.get("contract", {})
      order = trade.get("order", {})
      order_status = trade.get("orderStatus", {})

      # Format legs if present
      legs = contract.get("legs", [])
      legs_str = "\n".join([
        f"  • {leg['action']} {leg['ratio']}x {leg['symbol']}"
        for leg in legs
      ]) if legs else "  • Single contract"

      message = (
        "✅ *Trade Executed*\n\n"
        f"*Contract:* {contract.get('symbol')}\n"
        f"*Legs:*\n{legs_str}\n"
        f"*Order Type:* {order.get('orderType')}\n"
        f"*Status:* {order_status.get('status')}\n"
        f"*Filled:* {order_status.get('filled')}\n"
        f"*Avg Price:* ${order_status.get('avgFillPrice', 0):.2f}"
      )

      await self.app.bot.send_message(
        chat_id=self.chat_id,
        text=message,
        parse_mode="Markdown",
      )
    except Exception as e:
      logger.error("Error formatting trade message: {}", str(e))
      await self.app.bot.send_message(
        chat_id=self.chat_id,
        text=trade_message,
        parse_mode="Markdown",
      )

  async def stop(self) -> None:
    """Stop the bot."""
    if self.app.updater:
      await self.app.updater.stop()
    await self.app.stop()
    await self.app.shutdown()
