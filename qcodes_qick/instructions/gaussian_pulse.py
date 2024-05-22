from typing import Any

from qcodes_qick.channels import DacChannel
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters import GainParameter, HzParameter, SecParameter
from qcodes_qick.protocol_base import HardwareSweep, SweepProgram
from qcodes_qick.instruction_base import QickInstruction
from qick.averager_program import QickSweep


class GaussianPulse(QickInstruction):
    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        name="GaussianPulse",
        **kwargs: Any,
    ):
        super().__init__(parent, name, **kwargs)
        self.dac = dac

        self.gain = GainParameter(
            name="gain",
            instrument=self,
            label="Pulse gain",
            initial_value=0.5,
        )
        self.freq = HzParameter(
            name="freq",
            instrument=self,
            label="Pulse frequency",
            initial_value=1e9,
            channel=self.dac,
        )
        self.sigma = SecParameter(
            name="sigma",
            instrument=self,
            label="Sigma of the gaussian",
            initial_value=100e-9,
            channel=self.dac,
        )
        self.length = SecParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            initial_value=400e-9,
            channel=self.dac,
        )

    def initialize(self, program: SweepProgram):
        program.add_gauss(
            ch=self.dac.channel,
            name=self.full_name,
            sigma=self.sigma.get_raw(),
            length=self.length.get_raw(),
        )
        program.set_pulse_registers(
            ch=self.dac.channel,
            style="arb",
            freq=self.freq.get_raw(),
            phase=0,
            gain=self.gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            waveform=self.full_name,
        )

    def play(self, program: SweepProgram):
        program.pulse(ch=self.dac.channel, t="auto")

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        if sweep.parameter is self.gain:
            reg = program.get_gen_reg(self.dac.channel, "gain")
            program.add_sweep(
                QickSweep(program, reg, sweep.start_int, sweep.stop_int, sweep.num)
            )
        elif sweep.parameter is self.freq:
            reg = program.get_gen_reg(self.dac.channel, "freq")
            self.add_sweep(
                QickSweep(program, reg, sweep.start / 1e6, sweep.stop / 1e6, sweep.num)
            )
        else:
            raise NotImplementedError(f"cannot sweep over {sweep.parameter.name}")
