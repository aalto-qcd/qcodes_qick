from qickodes.instruments import QickInstrument
from qickodes.protocol_base import HardwareSweep, SoftwareSweep
from importlib.metadata import PackageNotFoundError, version

__all__ = ["HardwareSweep", "QickInstrument", "SoftwareSweep"]

try:
    __version__ = version("qickodes")
except PackageNotFoundError:
    __version__ = "unknown"
