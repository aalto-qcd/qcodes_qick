from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import ManualParameter
from qcodes.validators import Numbers, Validator
from qick.asm_v2 import QickSweep

from qcodes_qick.instruments import QickInstrument

if TYPE_CHECKING:
    from qcodes.instrument import InstrumentModule


class SweepableNumbers(Validator):
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


class SweepableParameter(ManualParameter):
    def __init__(
        self,
        name: str,
        instrument: InstrumentModule,
        label: str,
        unit: str,
        vals: SweepableNumbers,
        initial_value: float,
        **kwargs,
    ):
        assert isinstance(instrument.parent, QickInstrument)
        self.qick_instrument: QickInstrument = instrument.parent
        super().__init__(
            name,
            instrument,
            label=label,
            unit=unit,
            set_parser=self.set_parser,
            vals=vals,
            initial_value=initial_value,
            **kwargs,
        )

    def set_parser(self, value: float | QickSweep) -> float | QickSweep:
        # keep track of all swept parameters of the instrument
        if isinstance(value, QickSweep):
            self.qick_instrument.swept_parameters.add(self)
        elif self in self.qick_instrument.swept_parameters:
            self.qick_instrument.swept_parameters.remove(self)
        return value
