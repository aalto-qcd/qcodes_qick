from qcodes_qick.envelope_base_v2 import DacEnvelope
from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters_v2 import SweepableNumbers, SweepableParameter
from qcodes_qick.protocol_base_v2 import SweepProgram


class Pulse(QickInstruction):
    """A pulse with an envelope.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    envelope : DacEnvelope
        The envelope of the pulse
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    def __init__(
        self,
        parent: QickInstrument,
        envelope: DacEnvelope,
        name="Pulse",
        **kwargs,
    ):
        super().__init__(
            parent, dacs=[envelope.dac], dac_envelopes=[envelope], name=name, **kwargs
        )

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
        self.phase = SweepableParameter(
            name="phase",
            instrument=self,
            label="Pulse phase",
            unit="deg",
            vals=SweepableNumbers(),
            initial_value=0,
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
            style="arb",
            freq=self.freq.get() / 1e6,
            phase=self.phase.get(),
            gain=self.gain.get(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            envelope=self.dac_envelopes[0].name,
        )

    def append_to(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.pulse(ch=self.dacs[0].channel_num, name=self.name, t="auto")
