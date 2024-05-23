from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import InstrumentChannel

from qcodes_qick.channels import DacChannel

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class MuxedDacTone(InstrumentChannel):
    parent: MuxedDacChannel

    def __init__(self, parent: MuxedDacChannel, name: str, **kwargs):
        super().__init__(parent, name, **kwargs)


class MuxedDacChannel(DacChannel):
    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, channel, **kwargs)
