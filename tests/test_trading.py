"""Tests for the trading client."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from ib_async.contract import Contract
from ib_async.order import Order
from src.ib_helper.trading import TradingClient

@pytest.fixture
def mock_ib() -> AsyncMock:
  """Create a mock IB interface."""
  mock = AsyncMock()
  mock.placeOrder = MagicMock()
  mock.cancelOrder = AsyncMock()
  return mock

@pytest.fixture
def mock_notification_bot() -> AsyncMock:
  """Create a mock notification bot."""
  mock = AsyncMock()
  mock.start = AsyncMock()
  mock.request_approval = AsyncMock(return_value=True)
  return mock

@pytest.fixture
def trading_client(mock_ib: AsyncMock, mock_notification_bot: AsyncMock) -> TradingClient:
  """Create a TradingClient instance with mocked dependencies."""
  client = TradingClient()
  client.ib = mock_ib
  client.notification_bot = mock_notification_bot
  client._bot_started = True
  return client

@pytest.mark.asyncio
async def test_execute_order_success(trading_client: TradingClient, mock_ib: AsyncMock) -> None:
  """Test successful order execution."""
  # Setup
  contract = Contract(conId=123, symbol="AAPL", secType="STK", exchange="SMART", currency="USD")
  action = "BUY"
  quantity = 100
  order_type = "MKT"

  # Mock trade object
  mock_trade = MagicMock()
  mock_trade.orderStatus.status = "Filled"
  mock_trade.orderStatus.avgFillPrice = 150.0
  mock_trade.dict.return_value = {
    "orderId": 1,
    "status": "Filled",
    "avgFillPrice": 150.0,
  }
  mock_ib.placeOrder.return_value = mock_trade

  # Execute
  result_str = await trading_client._execute_order(
    contract=contract,
    action=action,
    quantity=quantity,
    order_type=order_type,
  )
  result = json.loads(result_str)

  # Verify
  assert "trade" in result
  assert "error" in result
  assert result["error"] is None
  assert result["trade"]["status"] == "Filled"
  assert result["trade"]["avgFillPrice"] == 150.0

  # Verify order was placed with correct parameters
  mock_ib.placeOrder.assert_called_once()
  placed_order = mock_ib.placeOrder.call_args[0][1]
  assert isinstance(placed_order, Order)
  assert placed_order.action == action
  assert placed_order.totalQuantity == quantity
  assert placed_order.orderType == order_type

@pytest.mark.asyncio
async def test_execute_order_not_approved(
  trading_client: TradingClient,
  mock_notification_bot: AsyncMock,
) -> None:
  """Test order execution when not approved."""
  # Setup
  contract = Contract(conId=123, symbol="AAPL", secType="STK", exchange="SMART", currency="USD")
  mock_notification_bot.request_approval.return_value = False

  # Execute
  result_str = await trading_client._execute_order(
    contract=contract,
    action="BUY",
    quantity=100,
    order_type="MKT",
  )
  result = json.loads(result_str)

  # Verify
  assert result["trade"] is None
  assert result["error"] == "Order not approved"
  mock_notification_bot.request_approval.assert_called_once()

@pytest.mark.asyncio
async def test_execute_order_timeout(
  trading_client: TradingClient,
  mock_ib: AsyncMock,
) -> None:
  """Test order execution timeout."""
  # Setup
  contract = Contract(conId=123, symbol="AAPL", secType="STK", exchange="SMART", currency="USD")

  # Mock trade object that stays in "Submitted" state
  mock_trade = MagicMock()
  mock_trade.orderStatus.status = "Submitted"
  mock_ib.placeOrder.return_value = mock_trade

  # Execute
  result_str = await trading_client._execute_order(
    contract=contract,
    action="BUY",
    quantity=100,
    order_type="MKT",
  )
  result = json.loads(result_str)

  # Verify
  assert result["trade"] is None
  assert result["error"] == "Order not filled"
  mock_ib.cancelOrder.assert_called_once_with(mock_trade.order)
