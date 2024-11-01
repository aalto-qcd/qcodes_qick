from qcodes import ManualParameter
from qcodes.validators import Bool

from qcodes_qick.channels_v2 import DacChannel
from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters_v2 import SweepableNumbers, SweepableParameter
from qcodes_qick.protocol_base_v2 import SweepProgram


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

        self.gain = SweepableParameter(
            name="gain",
            instrument=self,
            label="Pulse gain",
            unit="DAC unit",
            vals=SweepableNumbers(-1, 1),
            initial_value=0.5,
        )
        self.freq = SweepableParameter(
            name="freq",
            instrument=self,
            label="Pulse frequency",
            unit="Hz",
            vals=SweepableNumbers(),
            initial_value=0,
        )
        self.length = SweepableParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            unit="sec",
            vals=SweepableNumbers(min_value=0),
            initial_value=400e-9,
        )
        self.phase_imbalance = ManualParameter(
            name="phase_imbalance",
            instrument=self,
            label="Phase offset to add to Q",
            unit="deg",
            vals=SweepableNumbers(),
            initial_value=0,
        )
        self.periodic = ManualParameter(
            name="periodic",
            instrument=self,
            label="Repeat the waveform until there is a new one in the queue",
            vals=Bool(),
            initial_value=False,
        )

    def copy(self, copy_name: str) -> "IQConstantPulse":
        copy = IQConstantPulse(self.parent, self.dac_i, self.dac_q, copy_name)
        copy.gain.set(self.gain.get())
        copy.freq.set(self.freq.get())
        copy.length.set(self.length.get())
        copy.phase_imbalance.set(self.phase_imbalance.get())
        copy.periodic.set(self.periodic.get())
        return copy

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        program.add_pulse(
            ch=self.dac_i.channel_num,
            name=f"{self.name}_i",
            ro_ch=self.dac_i.matching_adc.get(),
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
            name=f"{self.name}_q",
            ro_ch=self.dac_q.matching_adc.get(),
            style="const",
            freq=self.freq.get() / 1e6,
            phase=90 + self.phase_imbalance.get(),
            gain=self.gain.get(),
            phrst=0,
            stdysel="zero",
            mode="periodic" if self.periodic.get() else "oneshot",
            length=self.length.get() * 1e6,
        )

    def append_to(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        # assert self in program.protocol.instructions
        program.pulse(ch=self.dac_i.channel_num, name=f"{self.name}_i", t="auto")
        program.pulse(ch=self.dac_q.channel_num, name=f"{self.name}_q", t="auto")
