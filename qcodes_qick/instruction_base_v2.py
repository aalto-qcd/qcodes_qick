from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qcodes.instrument import InstrumentModule
from qcodes.parameters import Parameter

if TYPE_CHECKING:
    from qcodes_qick.channels_v2 import AdcChannel, DacChannel
    from qcodes_qick.envelope_base_v2 import DacEnvelope
    from qcodes_qick.instruments import QickInstrument
    from qcodes_qick.protocol_base import SweepProgram


class QickInstruction(InstrumentModule):
    """Base class for an instruction.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    dacs : Sequence[DacChannel]
        The DAC channels to use.
    adcs : Sequence[AdcChannel]
        The ADC channels to use.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    parent: QickInstrument

    def __init__(
        self,
        parent: QickInstrument,
        dacs: Sequence[DacChannel] = (),
        adcs: Sequence[AdcChannel] = (),
        dac_envelopes: Sequence[DacEnvelope] = (),
        name: str = "QickInstruction",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        assert parent.tproc_version.get() == 2
        parent.add_submodule(name, self)
        self.dacs = dacs
        self.adcs = adcs
        self.dac_envelopes = dac_envelopes

        self.dac_channel_nums = Parameter(
            name="dac_channel_nums",
            instrument=self,
            label="DAC channel numbers",
            initial_cache_value=[dac.channel_num for dac in dacs],
        )
        self.adc_channel_nums = Parameter(
            name="adc_channel_nums",
            instrument=self,
            label="ADC channel numbers",
            initial_cache_value=[adc.channel_num for adc in adcs],
        )
        self.dac_envelope_names = Parameter(
            name="dac_envelope_names",
            instrument=self,
            label="Names of DAC envelopes used in this instruction",
            initial_cache_value=[e.name for e in dac_envelopes],
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
