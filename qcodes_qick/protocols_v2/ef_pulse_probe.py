from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import ManualParameter
from qcodes.validators import Ints

from qcodes_qick.protocol_base_v2 import SweepProgram, SweepProtocol

if TYPE_CHECKING:
    from qick.qick_asm import QickConfig

    from qcodes_qick.instruction_base_v2 import QickInstruction
    from qcodes_qick.instructions_v2.readout import Readout
    from qcodes_qick.instruments import QickInstrument


class EfPulseProbeProtocol(SweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        ge_pi_pulse: QickInstruction,
        ef_pulse: QickInstruction,
        readout: Readout,
        name="EfPulseProbeProtocol",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.instructions = [ge_pi_pulse, ef_pulse, readout]
        self.ge_pi_pulse = ge_pi_pulse
        self.ef_pulse = ef_pulse
        self.readout = readout

        self.ef_pulse_count = ManualParameter(
            name="ef_pulse_count",
            instrument=self,
            label="Number of ef pulses",
            vals=Ints(min_value=0),
            initial_value=1,
        )

    def generate_program(
        self, soccfg: QickConfig, hardware_loop_counts: dict[str, int]
    ):
        return EfPulseProbeProgram(soccfg, self, hardware_loop_counts)


class EfPulseProbeProgram(SweepProgram):
    protocol: EfPulseProbeProtocol

    def _body(self, cfg: dict):  # noqa: ARG002
        self.protocol.ge_pi_pulse.append_to(self)
        for _ in range(self.protocol.ef_pulse_count.get()):
            self.protocol.ef_pulse.append_to(self)
        self.protocol.ge_pi_pulse.append_to(self)
        self.protocol.readout.append_to(self)
