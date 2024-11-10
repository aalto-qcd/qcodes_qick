from __future__ import annotations

from typing import TYPE_CHECKING

import qick.asm_v2

from qcodes_qick.macro_base_v2 import Macro
from qcodes_qick.parameters_v2 import SweepableParameter

if TYPE_CHECKING:
    from qick.asm_v2 import QickParam

    from qcodes_qick.instrument_v2 import QickInstrument


class Delay(Macro):
    """Increment the reference time.

    This will have the effect of delaying all timed instructions executed after this one.

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
        t: float | QickParam,
    ) -> None:
        qick_macro = qick.asm_v2.Delay(t=t * 1e6, auto=False)
        super().__init__(parent, "Delay", qick_macro)

        self.t = SweepableParameter(
            name="t",
            instrument=self,
            label="Time",
            unit="sec",
            initial_value=t,
            settable=False,
        )
