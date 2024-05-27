from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes_qick.protocol_base import SimpleSweepProtocol

if TYPE_CHECKING:
    from qcodes_qick.instructions.readout_pulse import ReadoutPulse
    from qcodes_qick.instruments import QickInstrument


class S21Protocol(SimpleSweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        readout_pulse: ReadoutPulse,
        name="S21Protocol",
        **kwargs,
    ):
        super().__init__(
            parent=parent,
            instructions=[
                readout_pulse,
            ],
            name=name,
            **kwargs,
        )
