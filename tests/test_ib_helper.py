"""Tests for the IB interface."""
import pytest
import pandas as pd
from io import StringIO
from src.ib_helper import IBInterface

@pytest.fixture
async def ib_interface() -> IBInterface:
  """Fixture to create and cleanup IB interface instance."""
  interface = IBInterface()
  yield interface
  # Cleanup
  if interface.ib and interface.ib.isConnected():
      interface.ib.disconnect()


@pytest.mark.asyncio
async def test_connection(ib_interface: IBInterface) -> None:
  """Test IB connection."""
  await ib_interface._connect()
  assert ib_interface.ib.isConnected()


@pytest.mark.asyncio
async def test_get_positions(ib_interface: IBInterface) -> None:
  """Test getting positions."""
  positions_json = await ib_interface.get_positions()

  # If no positions, check the expected message
  if positions_json == "No open positions found.":
      return

  # If positions exist, validate the JSON structure
  positions = pd.read_json(StringIO(positions_json))
  required_columns = ["contractId", "avgCost", "contract", "position"]
  assert all(col in positions.columns for col in required_columns)
