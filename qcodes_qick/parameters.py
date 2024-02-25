from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import ManualParameter

if TYPE_CHECKING:
    from qcodes_qick.channels import QickAdcChannel, QickDacChannel


class QuantizedParameter(ManualParameter):

    def __init__(self, name: str, **kwargs):
        super().__init__(
            name, get_parser=self.int2float, set_parser=self.float2int, **kwargs
        )

    def int2float(i: int) -> float: ...

    def float2int(f: float) -> int: ...


class DacHzParameter(QuantizedParameter):
    """Frequency parameter with automatic rounding to a multiple of the frequency unit of the specified DAC channel (and optionally also an ADC channel). The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(self, name: str, instrument: QickDacChannel, **kwargs):
        self.int2float = instrument.reg2hz
        self.float2int = instrument.hz2reg
        super().__init__(name, instrument=instrument, unit="Hz", **kwargs)


class AdcHzParameter(QuantizedParameter):
    """Frequency parameter with automatic rounding to a multiple of the frequency unit of the specified ADC channel (and optionally also an DAC channel). The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(self, name: str, instrument: QickAdcChannel, **kwargs):
        self.int2float = instrument.reg2hz
        self.float2int = instrument.hz2reg
        super().__init__(name, instrument=instrument, unit="Hz", **kwargs)


class DacDegParameter(QuantizedParameter):
    """Phase parameter with automatic rounding to a multiple of the phase unit of the specified DAC channel. The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(self, name: str, instrument: QickDacChannel, **kwargs):
        self.int2float = instrument.reg2deg
        self.float2int = instrument.deg2reg
        super().__init__(name=name, instrument=instrument, unit="deg", **kwargs)


class DacSecParameter(QuantizedParameter):
    """Time parameter with automatic rounding to a multiple of the clock period of the specified DAC channel. The `get_raw()` method returns the time in the number of clock cycles (int)."""

    def __init__(self, name: str, instrument: QickDacChannel, **kwargs):
        self.int2float = instrument.cycles2sec
        self.float2int = instrument.sec2cycles
        super().__init__(name=name, instrument=instrument, unit="sec", **kwargs)


class AdcSecParameter(QuantizedParameter):
    """Time parameter with automatic rounding to a multiple of the clock period of the specified ADC channel. The `get_raw()` method returns the time in the number of clock cycles (int)."""

    def __init__(self, name: str, instrument: QickAdcChannel, **kwargs):
        self.int2float = instrument.cycles2sec
        self.float2int = instrument.sec2cycles
        super().__init__(name=name, instrument=instrument, unit="sec", **kwargs)
