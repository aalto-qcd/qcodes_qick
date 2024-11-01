from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qcodes import ManualParameter
from qcodes.validators import Bool

from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.parameters_v2 import SweepableNumbers, SweepableParameter

if TYPE_CHECKING:
    from qick.asm_v2 import QickParam

    from qcodes_qick.channels_v2 import AdcChannel
    from qcodes_qick.instruments import QickInstrument
    from qcodes_qick.protocol_base_v2 import SweepProgram


class TriggerAdcs(QickInstruction):
    """Trigger the specified ADC channels.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    adc : Sequence[AdcChannel]
        The ADC channels to trigger.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    def __init__(
        self,
        parent: QickInstrument,
        adcs: Sequence[AdcChannel] | AdcChannel,
        t: float | QickParam = 0,
        ddr4: bool = False,
        name="TriggerAdcs",
        **kwargs,
    ):
        if not isinstance(adcs, Sequence):
            adcs = [adcs]
        super().__init__(parent, adcs=adcs, name=name, **kwargs)

        self.t = SweepableParameter(
            name="t",
            instrument=self,
            label="Trigger time relative to the last DelayAuto",
            unit="sec",
            vals=SweepableNumbers(),
            initial_value=t,
        )
        self.ddr4 = ManualParameter(
            name="ddr4",
            instrument=self,
            label="Trigger the DDR4 buffer",
            vals=Bool(),
            initial_value=ddr4,
        )

    def initialize(self, program: SweepProgram):  # noqa: ARG002
        """Initialize the DDR4 buffer if necessary. This is done immediately and is not a part of the program.

        Parameters
        ----------
        program : SweepProgram (not used)
        """
        if self.ddr4:
            ddr4_channel = self.parent.ddr4_buffer.selected_adc_channel.get()
            ddr4_num_transfers = self.parent.ddr4_buffer.num_transfers.get()
            assert len(self.adcs) == 1
            assert ddr4_channel == self.adcs[0].channel_num
            self.parent.soc.arm_ddr4(ch=ddr4_channel, nt=ddr4_num_transfers)

    def append_to(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.trigger(
            ros=[adc.channel_num for adc in self.adcs],
            t=self.t.get() * 1e6,
            ddr4=self.ddr4.get(),
        )
