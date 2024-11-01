from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes_qick.instructions_v2.delay_auto import DelayAuto
from qcodes_qick.protocol_base_v2 import SimpleSweepProtocol

if TYPE_CHECKING:
    from qcodes_qick.instruction_base_v2 import QickInstruction
    from qcodes_qick.instructions_v2.readout import Readout
    from qcodes_qick.instruments import QickInstrument


class EfRamseyProtocol(SimpleSweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        ge_pi_pulse: QickInstruction,
        ge_half_pi_pulse: QickInstruction,
        ef_half_pi_pulse: QickInstruction,
        readout: Readout,
        name="EfRamseyProtocol",
        **kwargs,
    ):
        self.delay = DelayAuto(parent)
        self.ef_half_pi_pulse_2 = ef_half_pi_pulse.copy(ef_half_pi_pulse.name + "_2")
        super().__init__(
            parent=parent,
            instructions=[
                ge_pi_pulse,
                ef_half_pi_pulse,
                self.delay,
                self.ef_half_pi_pulse_2,
                ge_half_pi_pulse,
                readout,
            ],
            name=name,
            **kwargs,
        )
