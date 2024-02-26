from __future__ import annotations

from typing import TYPE_CHECKING, Union

from qcodes import ManualParameter
from qcodes.validators import Numbers

if TYPE_CHECKING:
    from qcodes_qick.channels import AdcChannel, DacChannel
    from qcodes_qick.instruments import QickInstrument


class QuantizedParameter(ManualParameter):

    def __init__(self, name: str, **kwargs):
        super().__init__(
            name, get_parser=self.int2float, set_parser=self.float2int, **kwargs
        )

    def int2float(i: int) -> float: ...

    def float2int(f: float) -> int: ...


class HzParameter(QuantizedParameter):
    """Frequency parameter with automatic rounding to a multiple of the frequency unit of the specified DAC/ADC channel. The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(self, name: str, channel: Union[DacChannel, AdcChannel], **kwargs):
        self.int2float = channel.reg2hz
        self.float2int = channel.hz2reg
        super().__init__(name, unit="Hz", **kwargs)


class DegParameter(QuantizedParameter):
    """Phase parameter with automatic rounding to a multiple of the phase unit of the specified DAC channel. The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(self, name: str, channel: DacChannel, **kwargs):
        self.int2float = channel.reg2deg
        self.float2int = channel.deg2reg
        super().__init__(name=name, unit="deg", **kwargs)


class SecParameter(QuantizedParameter):
    """Time parameter with automatic rounding to a multiple of the clock period of the specified DAC/ADC channel. The `get_raw()` method returns the time in the number of clock cycles."""

    def __init__(self, name: str, channel: Union[DacChannel, AdcChannel], **kwargs):
        self.int2float = channel.cycles2sec
        self.float2int = channel.sec2cycles
        super().__init__(name=name, unit="sec", **kwargs)


class TProcSecParameter(QuantizedParameter):
    """Time parameter with automatic rounding to a multiple of the tProc clock period. The `get_raw()` method returns the time in the number of clock cycles."""

    def __init__(self, name: str, qick_instrument: QickInstrument, **kwargs):
        self.int2float = qick_instrument.cycles2sec_tproc
        self.float2int = qick_instrument.sec2cycles_tproc
        super().__init__(name=name, unit="sec", **kwargs)


class GainParameter(QuantizedParameter):
    """Gain parameter with automatic rounding to a multiple of the gain unit. The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, vals=Numbers(-1, 32767 / 32768), **kwargs)

    def int2float(i: int) -> float:
        return i / 32768

    def float2int(f: float) -> int:
        return round(f * 32768)
