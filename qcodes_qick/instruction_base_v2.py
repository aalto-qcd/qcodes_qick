from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qcodes.instrument import InstrumentModule

if TYPE_CHECKING:
    from qcodes_qick.channels import AdcChannel, DacChannel
    from qcodes_qick.instruments import QickInstrument
    from qcodes_qick.protocol_base_v2 import HardwareSweep, SweepProgram


class QickInstruction(InstrumentModule):
    """Base class for an instruction.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    adc : AdcChannel
        The ADC channel to use.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.dacs: Sequence[DacChannel] = []
        self.adcs: Sequence[AdcChannel] = []
        assert parent.tproc_version.get() == 2
        parent.add_submodule(name, self)

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

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        """Add a sweep over one of my parameters to a program.

        Parameters
        ----------
        program : SweepProgram
        sweep: HardwareSweep
        """
        raise NotImplementedError(f"cannot sweep over {sweep.parameter.name}")
