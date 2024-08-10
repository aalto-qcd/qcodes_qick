from __future__ import annotations

from qcodes.validators import Numbers, Validator
from qick.asm_v2 import QickSweep


class MaybeSweep(Validator[float | QickSweep]):
    def __init__(
        self,
        min_value: float = -float("inf"),
        max_value: float = float("inf"),
    ):
        self.numbers = Numbers(min_value, max_value)
        self._valid_values = (min_value, max_value)

    def validate(self, value: float | QickSweep, context: str = ""):
        if isinstance(value, QickSweep):
            self.numbers.validate(value.minval(), context)
            self.numbers.validate(value.maxval(), context)
        else:
            self.numbers.validate(value, context)
