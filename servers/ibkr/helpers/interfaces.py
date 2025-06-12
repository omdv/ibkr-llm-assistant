"""Main IB interface combining all functionality."""
from .market_data import MarketDataClient
from .contracts import ContractClient
from .scanners import ScannerClient
from .positions import PositionClient
from .trading import TradingClient

class IBInterface(
  MarketDataClient,
  ContractClient,
  ScannerClient,
  PositionClient,
  TradingClient,
):
  """Main IB interface combining all functionality."""
