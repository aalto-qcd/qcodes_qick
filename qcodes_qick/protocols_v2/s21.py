from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes_qick.protocol_base_v2 import SimpleSweepProtocol

if TYPE_CHECKING:
    from qcodes_qick.instructions_v2.readout import Readout
    from qcodes_qick.instruments import QickInstrument


class S21Protocol(SimpleSweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        readout: Readout,
        name="S21Protocol",
        **kwargs,
    ):
        super().__init__(
            parent=parent,
            instructions=[
                readout,
            ],
            name=name,
            **kwargs,
        )
