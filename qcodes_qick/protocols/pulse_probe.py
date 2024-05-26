from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qcodes import ManualParameter
from qcodes.validators import Ints
from qick.qick_asm import QickConfig

from qcodes_qick.protocol_base import HardwareSweep, SweepProgram, SweepProtocol

if TYPE_CHECKING:
    from qcodes_qick.instruction_base import QickInstruction
    from qcodes_qick.instructions.readout_pulse import ReadoutPulse
    from qcodes_qick.instruments import QickInstrument


class PulseProbeProtocol(SweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        qubit_pulse: QickInstruction,
        readout_pulse: ReadoutPulse,
        name="PulseProbeProtocol",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.instructions = [qubit_pulse, readout_pulse]
        self.qubit_pulse = qubit_pulse
        self.readout_pulse = readout_pulse

        self.qubit_pulse_count = ManualParameter(
            name="qubit_pulse_count",
            instrument=self,
            label="Number of qubit pulses",
            vals=Ints(min_value=0),
            initial_value=1,
        )

    def generate_program(
        self, soccfg: QickConfig, hardware_sweeps: Sequence[HardwareSweep] = ()
    ):
        return PulseProbeProgram(soccfg, self, hardware_sweeps)


class PulseProbeProgram(SweepProgram):
    protocol: PulseProbeProtocol

    def body(self):
        for _ in range(self.protocol.qubit_pulse_count.get()):
            self.protocol.qubit_pulse.play(self)
        self.protocol.readout_pulse.play(self, wait_for_adc=True)
