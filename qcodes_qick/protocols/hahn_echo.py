from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes_qick.instructions.delay import Delay
from qcodes_qick.protocol_base import SimpleSweepProtocol

if TYPE_CHECKING:
    from qcodes_qick.instruction_base import QickInstruction
    from qcodes_qick.instructions.readout_pulse import ReadoutPulse
    from qcodes_qick.instruments import QickInstrument


class HahnEchoProtocol(SimpleSweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        half_pi_pulse: QickInstruction,
        readout_pulse: ReadoutPulse,
        name="HahnEchoProtocol",
        **kwargs,
    ):
        self.delay = Delay(parent, half_pi_pulse.dacs[0])
        super().__init__(
            parent=parent,
            instructions=[
                half_pi_pulse,
                self.delay,
                half_pi_pulse,
                half_pi_pulse,
                self.delay,
                half_pi_pulse,
                readout_pulse,
            ],
            name=name,
            **kwargs,
        )
