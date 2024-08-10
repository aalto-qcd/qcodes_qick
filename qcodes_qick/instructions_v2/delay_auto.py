from qcodes import ManualParameter
from qcodes.validators import Numbers

from qcodes_qick.channels_v2 import DacChannel
from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.protocol_base_v2 import SweepProgram
from qcodes_qick.validators import MaybeSweep


class DelayAuto(QickInstruction):
    """Add a delay, counting from the end of the last pulse or readout.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    dac : DacChannel
        The DAC channel to add the delay to.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        name="DelayAuto",
        **kwargs,
    ):
        super().__init__(parent, dacs=[dac], name=name, **kwargs)

        self.time = ManualParameter(
            name="time",
            instrument=self,
            label="Delay time",
            unit="sec",
            vals=MaybeSweep(Numbers(min_value=0)),
            initial_value=1e-6,
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """

    def play(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.delay_auto(self.time.get() * 1e6)
