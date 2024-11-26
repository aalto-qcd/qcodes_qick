from __future__ import annotations

from typing import TYPE_CHECKING

import qick.asm_v2
from qcodes import Parameter

from qcodes_qick.macro_base_v2 import Macro
from qcodes_qick.parameters_v2 import SweepableParameter

if TYPE_CHECKING:
    from qick.asm_v2 import QickParam

    from qcodes_qick.instrument_v2 import QickInstrument


class DelayAuto(Macro):
    """Set the reference time to the end of the last pulse/readout, plus the specified value.

    You can select whether this accounts for pulses, readout windows, or both.

    Parameters
    ----------
    parent : QickInstrument
        Where this is done.
    t : float | QickParam
        The number to add to the reference time.
    """

    def __init__(
        self,
        parent: QickInstrument,
        t: float | QickParam = 0,
        wait_for_dacs: bool = True,
        wait_for_adcs: bool = True,
    ) -> None:
        name = parent.append_counter_to_macro_name("DelayAuto")
        qick_macro = qick.asm_v2.Delay(
            t=t * 1e6, auto=True, gens=wait_for_dacs, ros=wait_for_adcs, tag=name
        )
        super().__init__(parent, name, qick_macro)

        self.t = SweepableParameter(
            name="t",
            instrument=self,
            label="Time",
            unit="sec",
            initial_value=t,
            settable=False,
        )
        self.wait_for_dacs = Parameter(
            name="wait_for_dacs",
            instrument=self,
            label="Wait for DACs",
            initial_cache_value=wait_for_dacs,
        )
        self.wait_for_adcs = Parameter(
            name="wait_for_adcs",
            instrument=self,
            label="Wait for ADCs",
            initial_cache_value=wait_for_adcs,
        )
