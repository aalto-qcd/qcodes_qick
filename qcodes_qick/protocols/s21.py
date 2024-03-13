from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qcodes_qick.protocol_base import HardwareSweep, SweepProgram, SweepProtocol
from qcodes_qick.instructions.readout_pulse import ReadoutPulse
from qick.qick_asm import QickConfig

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class S21Protocol(SweepProtocol):

    def __init__(
        self,
        parent: QickInstrument,
        readout_pulse: ReadoutPulse,
        name="S21Protocol",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.instructions = {readout_pulse}
        self.readout_pulse = readout_pulse

    def generate_program(
        self, soccfg: QickConfig, hardware_sweeps: Sequence[HardwareSweep] = ()
    ):
        return S21Program(soccfg, self, hardware_sweeps)


class S21Program(SweepProgram):

    protocol: S21Protocol

    def body(self):
        self.protocol.readout_pulse.play(self, wait_for_adc=True)
