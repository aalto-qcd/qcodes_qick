from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes_qick.instructions_v2.delay_auto import DelayAuto
from qcodes_qick.protocol_base_v2 import SimpleSweepProtocol

if TYPE_CHECKING:
    from qcodes_qick.instruction_base_v2 import QickInstruction
    from qcodes_qick.instructions_v2.readout import Readout
    from qcodes_qick.instruments import QickInstrument


class RamseyWithDriveProtocol(SimpleSweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        half_pi_pulse: QickInstruction,
        drive_pulse: QickInstruction,
        readout: Readout,
        name="RamseyWithDriveProtocol",
        **kwargs,
    ):
        self.half_pi_pulse_2 = half_pi_pulse.copy(half_pi_pulse.name + "_2")
        sync = DelayAuto(parent)
        super().__init__(
            parent=parent,
            instructions=[
                half_pi_pulse,
                sync,
                drive_pulse,
                sync,
                self.half_pi_pulse_2,
                readout,
            ],
            name=name,
            **kwargs,
        )
