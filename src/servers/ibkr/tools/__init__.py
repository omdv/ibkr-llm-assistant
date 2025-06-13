"""MCP server setup."""
from fastmcp import FastMCP

from src.servers.ibkr.helpers import IBInterface

ibkr = FastMCP("ibkr")

# Initialize shared interface
ib_interface = IBInterface()

# Import all tools
from .positions import *
from .scanner import *
from .contracts import *
from .trading import *
