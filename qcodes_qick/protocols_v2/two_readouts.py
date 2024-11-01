from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes_qick.protocol_base_v2 import SimpleSweepProtocol

if TYPE_CHECKING:
    from qcodes_qick.instruction_base_v2 import QickInstruction
    from qcodes_qick.instructions_v2.readout import Readout
    from qcodes_qick.instruments import QickInstrument


class TwoReadoutsProtocol(SimpleSweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        pi_pulse: QickInstruction,
        readout: Readout,
        name="TwoReadoutsProtocol",
        **kwargs,
    ):
        self.pi_pulse_2 = pi_pulse.copy(pi_pulse.name + "_2")
        super().__init__(
            parent=parent,
            instructions=[
                pi_pulse,
                readout,
                self.pi_pulse_2,
                readout,
            ],
            name=name,
            **kwargs,
        )
