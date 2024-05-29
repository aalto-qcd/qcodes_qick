from qick.averager_program import QickSweep

from qcodes_qick.channels import DacChannel
from qcodes_qick.instruction_base import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters import GainParameter, HzParameter, SecParameter
from qcodes_qick.protocol_base import HardwareSweep, SweepProgram


class ConstantPulse(QickInstruction):
    """Rectangular pulse.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    dac : DacChannel
        The DAC channel to use.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        name="ConstantPulse",
        **kwargs,
    ):
        super().__init__(parent, dacs=[dac], name=name, **kwargs)

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
            initial_value=0,
            channel=self.dacs[0],
        )
        self.length = SecParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            initial_value=400e-9,
            channel=self.dacs[0],
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        program.set_pulse_registers(
            ch=self.dacs[0].channel_num,
            style="const",
            freq=self.freq.get_raw(),
            phase=0,
            gain=self.gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=self.length.get_raw(),
        )

    def play(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.pulse(ch=self.dacs[0].channel_num, t="auto")

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        """Add a sweep over one of my parameters to a program.

        Parameters
        ----------
        program : SweepProgram
        sweep: HardwareSweep
        """
        if sweep.parameter is self.gain:
            reg = program.get_gen_reg(self.dacs[0].channel_num, "gain")
            program.add_sweep(
                QickSweep(program, reg, sweep.start_int, sweep.stop_int, sweep.num)
            )
        elif sweep.parameter is self.freq:
            reg = program.get_gen_reg(self.dacs[0].channel_num, "freq")
            program.add_sweep(
                QickSweep(program, reg, sweep.start / 1e6, sweep.stop / 1e6, sweep.num)
            )
        else:
            raise NotImplementedError(
                f"cannot perform a hardware sweep over {sweep.parameter.name}"
            )
