from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qick.qick_asm import QickConfig

from qcodes_qick.instructions.delay import Delay
from qcodes_qick.instructions.set_phase import SetPhase
from qcodes_qick.protocol_base import HardwareSweep, SweepProgram, SweepProtocol

if TYPE_CHECKING:
    from qick.qick_asm import QickConfig

    from qcodes_qick.instruction_base import QickInstruction
    from qcodes_qick.instructions.readout import Readout
    from qcodes_qick.instruments import QickInstrument


class RamseyProtocol(SweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        half_pi_pulse: QickInstruction,
        readout: Readout,
        name="RamseyProtocol",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.half_pi_pulse = half_pi_pulse
        self.readout = readout
        self.delay = Delay(parent, half_pi_pulse.dacs[0])
        self.set_phase = SetPhase(parent, half_pi_pulse.dacs[0])
        self.instructions = [half_pi_pulse, readout, self.delay, self.set_phase]

    def generate_program(
        self, soccfg: QickConfig, hardware_sweeps: Sequence[HardwareSweep] = ()
    ):
        return RamseyProgram(soccfg, self, hardware_sweeps)


class RamseyProgram(SweepProgram):
    protocol: RamseyProtocol

    def body(self):
        self.protocol.set_phase.dac_phase_reg.set_to(0)
        self.protocol.half_pi_pulse.append_to(self)
        self.protocol.delay.append_to(self)
        self.protocol.set_phase.append_to(self)
        self.protocol.half_pi_pulse.append_to(self)
        self.protocol.readout.append_to(self)
