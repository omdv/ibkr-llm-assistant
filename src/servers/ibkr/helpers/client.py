"""Base IB client connection handling."""
import asyncio
import datetime as dt
from loguru import logger
from ib_async import IB

from src.servers.ibkr.settings import Settings

class IBClient:
  """Base IB client connection handling. No public methods."""

  def __init__(self) -> None:
    """Initialize IB interface."""
    self.config = Settings()
    self.ib = IB()

  async def _connect(self) -> None:
    """Create and connect IB client."""
    if self.ib.isConnected():
      return

    host = self.config.ib_gateway_host
    port = self.config.ib_gateway_port

    try:
      logger.debug("Connecting to IB on {}:{}", host, port)
      await self.ib.connectAsync(
        host=host,
        port=port,
        clientId=dt.datetime.now(dt.UTC).strftime("%H%M%S"),
        timeout=20,
        readonly=False,
      )
      self.ib.RequestTimeout = 20
      logger.debug("Connected to IB on {}:{}", host, port)
    except Exception as e:
      logger.error("Error connecting to IB: {}", e)
      raise

  async def send_command_to_ibc(self, command: str) -> None:
    """Send a command to the IBC Command Server.

    Args:
        command: The command to send to the IBC Command Server

    """
    if not command:
      logger.error("Error: you must supply a valid IBC command")
      return

    host = self.config.ib_gateway_host
    port = self.config.ib_command_server_port

    try:
      # Create connection
      reader, writer = await asyncio.open_connection(host, port)

      # Send command
      writer.write(command.encode() + b"\n")
      await writer.drain()

      # Close connection
      writer.close()
      await writer.wait_closed()

      logger.debug("Successfully sent command to IBC: {}", command)
    except Exception as e:
      logger.error("Error sending command to IBC: {}", str(e))
      raise

  def __del__(self) -> None:
    """Disconnect from IB."""
    try:
      if self.ib and self.ib.isConnected():
        self.ib.disconnect()
    except Exception:
      logger.debug("Error disconnecting from IB")
