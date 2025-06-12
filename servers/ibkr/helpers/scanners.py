"""Scanner operations."""
from loguru import logger

from defusedxml import ElementTree
from ib_async.objects import ScannerSubscription, TagValue

from .client import IBClient

class ScannerClient(IBClient):
  """Scanner operations.

  Available public methods:
    - get_scanner_instrument_codes: get scanner instrument codes
    - get_scanner_location_codes: get scanner location codes
    - get_scanner_filter_codes: get scanner filter codes
    - get_scanner_results: get scanner results
  """

  async def get_scanner_instrument_codes(self) -> list[str]:
    """Get scanner instrument codes."""
    try:
      await self._connect()
      xml_parameters = await self.ib.reqScannerParametersAsync()
      tree = ElementTree.fromstring(xml_parameters)
      tags = [elem.text for elem in tree.findall(".//Instrument/type")]
    except Exception as e:
      logger.error("Error getting scanner instrument codes: {}", str(e))
      raise
    else:
      return tags

  async def get_scanner_location_codes(self) -> list[str]:
    """Get scanner location codes."""
    try:
      await self._connect()
      xml_parameters = await self.ib.reqScannerParametersAsync()
      tree = ElementTree.fromstring(xml_parameters)
      tags = [elem.text for elem in tree.findall(".//Location/locationCode")]
    except Exception as e:
      logger.error("Error getting scanner location codes: {}", str(e))
      raise
    else:
      return tags

  async def get_scanner_filter_codes(self) -> list[str]:
    """Get scanner filter codes."""
    try:
      await self._connect()
      xml_parameters = await self.ib.reqScannerParametersAsync()
      tree = ElementTree.fromstring(xml_parameters)
      tags = [elem.text for elem in tree.findall(".//AbstractField/code")]
    except Exception as e:
      logger.error("Error getting scanner filter codes: {}", str(e))
      raise
    else:
      return tags

  async def get_scanner_results(
      self,
      instrument_code: str,
      location_code: str,
      tags: list[(str, str)],
      scan_code: str | None = "TOP_PERC_GAIN",
      number_of_rows: int | None = 100,
    ) -> list[str]:
    """Get scanner results.

    Args:
      instrument_code: Instrument code to get scanner results for.
      location_code: Location code to get scanner results for.
      tags: Tags to get scanner results for.
      scan_code: Scan code to get scanner results for.
      number_of_rows: Number of rows to get scanner results for.

    Returns:
      List of symbols for the given scanner results.

    """
    try:
      logger.debug("Getting scanner results with tags: {}", tags)
      cleaned_tags = [TagValue(tag.split("=")[0], tag.split("=")[1]) for tag in tags]

      await self._connect()
      sub_object = ScannerSubscription(
        numberOfRows=number_of_rows,
        instrument=instrument_code,
        locationCode=location_code,
        scanCode=scan_code,
      )
      active_sub = self.ib.reqScannerSubscription(sub_object, [], cleaned_tags)
      scanner_data = await self.ib.reqScannerDataAsync(sub_object, [], cleaned_tags)
      self.ib.cancelScannerSubscription(active_sub)

      symbols = [row.contractDetails.contract.symbol for row in scanner_data]
    except Exception as e:
      logger.error("Error getting scanner results: {}", str(e))
      raise
    else:
      return symbols
