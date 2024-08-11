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


class PulseProbeProtocol(SweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        qubit_pulse: QickInstruction,
        readout: Readout,
        name="PulseProbeProtocol",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.instructions = [qubit_pulse, readout]
        self.qubit_pulse = qubit_pulse
        self.readout = readout

        self.qubit_pulse_count = ManualParameter(
            name="qubit_pulse_count",
            instrument=self,
            label="Number of qubit pulses",
            vals=Ints(min_value=0),
            initial_value=1,
        )

    def generate_program(
        self, soccfg: QickConfig, hardware_loop_counts: dict[str, int]
    ):
        return PulseProbeProgram(soccfg, self, hardware_loop_counts)


class PulseProbeProgram(SweepProgram):
    protocol: PulseProbeProtocol

    def _body(self, cfg: dict):  # noqa: ARG002
        for _ in range(self.protocol.qubit_pulse_count.get()):
            self.protocol.qubit_pulse.append_to(self)
        self.protocol.readout.append_to(self)
