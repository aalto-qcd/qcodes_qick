from qcodes import ManualParameter
from qcodes.validators import Numbers

from qcodes_qick.channels_v2 import DacChannel
from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.protocol_base_v2 import SweepProgram
from qcodes_qick.validators import MaybeSweep


class GaussianDragPulse(QickInstruction):
    """Gaussian pulse with DRAG.

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
        name="GaussianDragPulse",
        **kwargs,
    ):
        super().__init__(parent, dacs=[dac], name=name, **kwargs)

        self.gain = ManualParameter(
            name="gain",
            instrument=self,
            label="Pulse gain",
            vals=MaybeSweep(Numbers(-1, 1)),
            initial_value=0.5,
        )
        self.freq = ManualParameter(
            name="freq",
            instrument=self,
            label="Pulse frequency",
            unit="Hz",
            vals=MaybeSweep(Numbers()),
            initial_value=0,
        )
        self.sigma = ManualParameter(
            name="sigma",
            instrument=self,
            label="Standard deviation of the gaussian",
            unit="sec",
            vals=Numbers(min_value=0),
            initial_value=100e-9,
        )
        self.length = ManualParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            unit="sec",
            vals=Numbers(min_value=0),
            initial_value=400e-9,
        )
        self.delta = ManualParameter(
            name="delta",
            instrument=self,
            label="Anharmonicity of the qubit",
            unit="Hz",
            vals=Numbers(),
            initial_value=-200e6,
        )
        self.alpha = ManualParameter(
            name="alpha",
            instrument=self,
            label="Alpha parameter of DRAG",
            vals=Numbers(),
            initial_value=0.5,
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        program.add_DRAG(
            ch=self.dacs[0].channel_num,
            name=self.full_name,
            sigma=self.sigma.get() * 1e6,
            length=self.length.get() * 1e6,
            delta=self.delta.get() / 1e6,
            alpha=self.alpha.get(),
        )
        program.add_pulse(
            ch=self.dacs[0].channel_num,
            name=self.full_name,
            ro_ch=self.dacs[0].matching_adc.get(),
            style="arb",
            freq=self.freq.get() / 1e6,
            phase=0,
            gain=self.gain.get(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            envelope=self.full_name,
        )

    def play(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.pulse(ch=self.dacs[0].channel_num, nem=self.full_name, t="auto")
