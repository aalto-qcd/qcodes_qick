from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes.instrument import InstrumentModule
from qcodes.parameters import Parameter

if TYPE_CHECKING:
    from qcodes_qick.channels_v2 import DacChannel
    from qcodes_qick.instruments import QickInstrument
    from qcodes_qick.protocol_base import SweepProgram


class DacEnvelope(InstrumentModule):
    """Base class for an envelope.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    dac : DacChannel
        The DAC channel.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    parent: QickInstrument

    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        name: str = "DacEnvelope",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        assert parent.tproc_version.get() == 2
        parent.add_submodule(name, self)
        self.dac = dac

        self.dac_channel_num = Parameter(
            name="dac_channel_num",
            instrument=self,
            label="DAC channel number",
            initial_cache_value=dac.channel_num,
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
