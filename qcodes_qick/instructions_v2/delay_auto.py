from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters_v2 import SweepableNumbers, SweepableParameter
from qcodes_qick.protocol_base_v2 import SweepProgram


class DelayAuto(QickInstruction):
    """Add a delay, counting from the end of the last pulse or readout.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    def __init__(
        self,
        parent: QickInstrument,
        name="DelayAuto",
        **kwargs,
    ):
        super().__init__(parent, name=name, **kwargs)

        self.time = SweepableParameter(
            name="time",
            instrument=self,
            label="Delay time",
            unit="sec",
            vals=SweepableNumbers(min_value=0),
            initial_value=0,
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """

    def append_to(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.delay_auto(self.time.get() * 1e6)
