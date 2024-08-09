from qcodes.parameters import ManualParameter
from qcodes.validators import Bool

from qcodes_qick.channels import DacChannel
from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters import (
    DegParameter,
    GainParameter,
    HzParameter,
    SecParameter,
)
from qcodes_qick.protocol_base_v2 import HardwareSweep, SweepProgram


class IQConstantPulse(QickInstruction):
    """Rectangular pulse for an IQ mixer.

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
        dac_i: DacChannel,
        dac_q: DacChannel,
        name="IQConstantPulse",
        **kwargs,
    ):
        super().__init__(parent, dacs=[dac_i, dac_q], name=name, **kwargs)
        self.dac_i = dac_i
        self.dac_q = dac_q

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
            channel=self.dac_i,
        )
        self.length = SecParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            initial_value=400e-9,
            channel=self.dac_i,
        )
        self.phase_imbalance = DegParameter(
            name="phase_imbalance",
            instrument=self,
            label="Phase offset to add to Q",
            initial_value=0,
            channel=self.dac_q,
        )
        self.periodic = ManualParameter(
            name="periodic",
            instrument=self,
            label="Repeat the waveform until there is a new one in the queue",
            vals=Bool(),
            initial_value=False,
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        program.add_pulse(
            ch=self.dac_i.channel_num,
            name=f"{self.full_name}_i",
            style="const",
            freq=self.freq.get() / 1e6,
            phase=0,
            gain=self.gain.get(),
            phrst=0,
            stdysel="zero",
            mode="periodic" if self.periodic.get() else "oneshot",
            length=self.length.get() * 1e6,
        )
        program.add_pulse(
            ch=self.dac_q.channel_num,
            name=f"{self.full_name}_q",
            style="const",
            freq=self.freq.get() / 1e6,
            phase=90 + self.phase_imbalance.get(),
            gain=self.gain.get(),
            phrst=0,
            stdysel="zero",
            mode="periodic" if self.periodic.get() else "oneshot",
            length=self.length.get() * 1e6,
        )

    def play(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        # assert self in program.protocol.instructions
        program.pulse(ch=self.dac_i.channel_num, name=f"{self.full_name}_i", t="auto")
        program.pulse(ch=self.dac_q.channel_num, name=f"{self.full_name}_q", t="auto")

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        """Add a sweep over one of my parameters to a program.

        Parameters
        ----------
        program : SweepProgram
        sweep: HardwareSweep
        """
        raise NotImplementedError(
            f"cannot perform a hardware sweep over {sweep.parameter.name}"
        )
