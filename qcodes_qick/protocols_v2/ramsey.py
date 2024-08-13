from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes_qick.instructions_v2.delay_auto import DelayAuto
from qcodes_qick.protocol_base_v2 import SimpleSweepProtocol

if TYPE_CHECKING:
    from qcodes_qick.instruction_base_v2 import QickInstruction
    from qcodes_qick.instructions_v2.readout import Readout
    from qcodes_qick.instruments import QickInstrument


class RamseyProtocol(SimpleSweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        half_pi_pulse: QickInstruction,
        readout: Readout,
        name="RamseyProtocol",
        **kwargs,
    ):
        self.delay = DelayAuto(parent, half_pi_pulse.dacs[0])
        self.half_pi_pulse_2 = half_pi_pulse.copy(half_pi_pulse.name + "_2")
        super().__init__(
            parent=parent,
            instructions=[
                half_pi_pulse,
                self.delay,
                self.half_pi_pulse_2,
                readout,
            ],
            name=name,
            **kwargs,
        )
