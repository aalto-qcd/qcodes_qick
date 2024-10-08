from qcodes_qick.channels_v2 import DacChannel
from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters_v2 import SweepableNumbers, SweepableParameter
from qcodes_qick.protocol_base_v2 import SweepProgram


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

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        program.add_pulse(
            ch=self.dacs[0].channel_num,
            name=self.name,
            ro_ch=self.dacs[0].matching_adc.get(),
            style="const",
            freq=self.freq.get() / 1e6,
            phase=0,
            gain=self.gain.get(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=self.length.get() * 1e6,
        )

    def append_to(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        # assert self in program.protocol.instructions
        program.pulse(ch=self.dacs[0].channel_num, name=self.name, t="auto")
