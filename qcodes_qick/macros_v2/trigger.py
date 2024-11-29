from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

import qick.asm_v2
from qcodes import Parameter

from qcodes_qick.channels_v2 import AdcChannel
from qcodes_qick.macro_base_v2 import Macro
from qcodes_qick.parameters_v2 import SweepableParameter

if TYPE_CHECKING:
    from qick.asm_v2 import QickParam

    from qcodes_qick.instrument_v2 import QickInstrument


class Trigger(Macro):
    """Trigger ADCs and output pins.

    Parameters
    ----------
    parent : QickInstrument
        Where to play the trigger.
    adcs : AdcChannel or Iterable[AdcChannel], optional
        ADC channels to trigger.
    pins : Iterable[int], optional
        Output pins to trigger (index in output pins list in QickConfig printout).
    t : float | QickParam, default=0
        Time relative to the last Delay or DelayAuto.
    ddr4 : bool, default=False
        Trigger the DDR4 buffer
    mr : bool, default=False
        Trigger the multi-rate buffer
    """

    def __init__(
        self,
        parent: QickInstrument,
        adcs: AdcChannel | Iterable[AdcChannel] = (),
        pins: Iterable[int] = (),
        t: float | QickParam = 0,
        ddr4: bool = False,
        mr: bool = False,
    ) -> None:
        if isinstance(adcs, AdcChannel):
            adcs = [adcs]
        assert all(adc.parent is parent for adc in adcs)
        name = parent.append_counter_to_macro_name("Trigger")
        super().__init__(parent, name, adcs=adcs)

        self.adc_channel_nums = Parameter(
            name="adc_channel_nums",
            instrument=self,
            label="ADC channel numbers",
            initial_cache_value=[adc.channel_num for adc in adcs],
        )
        self.pins = Parameter(
            name="pins",
            instrument=self,
            label="Pin numbers",
            initial_cache_value=pins,
        )
        self.t = SweepableParameter(
            name="t",
            instrument=self,
            label="Time",
            unit="sec",
            initial_value=t,
        )
        self.ddr4 = Parameter(
            name="ddr4",
            instrument=self,
            label="DDR4 buffer",
            initial_cache_value=ddr4,
        )
        self.mr = Parameter(
            name="mr",
            instrument=self,
            label="Multi-rate buffer",
            initial_cache_value=mr,
        )

    def create_qick_macro(self) -> qick.asm_v2.Macro:
        return qick.asm_v2.Trigger(
            ros=[adc.channel_num for adc in self.adcs],
            pins=self.pins.get(),
            t=self.t.qick_param * 1e6,
            width=None,
            ddr4=self.ddr4.get(),
            mr=self.mr.get(),
            tag=self.short_name,
        )
