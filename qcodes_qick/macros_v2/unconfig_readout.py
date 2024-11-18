from __future__ import annotations

from typing import TYPE_CHECKING

import qick.asm_v2

from qcodes_qick.macro_base_v2 import Macro
from qcodes_qick.parameters_v2 import SweepableParameter

if TYPE_CHECKING:
    from qick.asm_v2 import QickParam

    from qcodes_qick.channels_v2 import AdcChannel
    from qcodes_qick.instrument_v2 import QickInstrument


class UnconfigReadout(Macro):
    """Revert the readout window config of an ADC to its default.

    Parameters
    ----------
    parent : QickInstrument
        Where to preform the readout.
    adc : AdcChannel
        The ADC channel.
    t : float | QickParam, default=0
        Time relative to the last Delay or DelayAuto.
    """

    def __init__(
        self,
        parent: QickInstrument,
        adc: AdcChannel,
        t: float | QickParam = 0,
    ) -> None:
        assert adc.parent is parent
        qick_macro = qick.asm_v2.ConfigReadout(
            ch=adc.channel_num,
            name=adc.short_name,
            t=t * 1e6,
        )
        super().__init__(
            parent,
            "UnconfigReadout",
            qick_macro,
            adcs=[adc],
        )

        self.t = SweepableParameter(
            name="t",
            instrument=self,
            label="Time",
            unit="sec",
            initial_value=t,
            settable=False,
        )
