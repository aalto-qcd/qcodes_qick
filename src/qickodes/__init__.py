from importlib.metadata import PackageNotFoundError, version

from qickodes.instruments import QickInstrument
from qickodes.protocol_base import HardwareSweep, SoftwareSweep

__all__ = ["HardwareSweep", "QickInstrument", "SoftwareSweep"]

try:
    __version__ = version("qickodes")
except PackageNotFoundError:
    __version__ = "unknown"
