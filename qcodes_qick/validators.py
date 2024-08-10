from __future__ import annotations

from qcodes.validators import Numbers, Validator
from qick.asm_v2 import QickSweep


class MaybeSweep(Validator[float | QickSweep]):
    def __init__(self, validator: Numbers):
        self._validator = validator
        self._valid_values = validator.valid_values

    def validate(self, value: float | QickSweep, context: str = ""):
        if isinstance(value, QickSweep):
            self._validator.validate(value.minval())
            self._validator.validate(value.maxval())
        else:
            self._validator.validate(value, context)
