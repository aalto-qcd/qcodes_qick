from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

from qcodes.instrument import InstrumentModule

if TYPE_CHECKING:
    from qcodes_qick.channels import AdcChannel, DacChannel
    from qcodes_qick.instruments import QickInstrument
    from qcodes_qick.protocol_base import HardwareSweep, SweepProgram


class QickInstruction(InstrumentModule):
    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, **kwargs: Any):
        """
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
        super().__init__(parent, name, **kwargs)
        self.dacs: Sequence[DacChannel] = []
        self.adcs: Sequence[AdcChannel] = []
        assert parent.tproc_version.get() == 1
        parent.add_submodule(name, self)

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        pass

    def play(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        pass

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        """Add a sweep over one of my parameters to a program.

        Parameters
        ----------
        program : SweepProgram
        sweep: HardwareSweep
        """
        raise NotImplementedError(f"cannot sweep over {sweep.parameter.name}")
