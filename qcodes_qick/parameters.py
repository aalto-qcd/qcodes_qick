from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import ManualParameter
from qcodes.validators import Numbers

if TYPE_CHECKING:
    from qcodes_qick.channels import QickAdcChannel, QickDacChannel


class DacHzParameter(ManualParameter):
    """Frequency parameter with automatic rounding to a multiple of the frequency unit of the specified DAC channel (and optionally also an ADC channel). The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(
        self,
        name: str,
        instrument: QickDacChannel,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instrument=instrument,
            get_parser=instrument.reg2hz,
            set_parser=instrument.hz2reg,
            vals=Numbers(),
            unit="Hz",
            **kwargs,
        )


class AdcHzParameter(ManualParameter):
    """Frequency parameter with automatic rounding to a multiple of the frequency unit of the specified ADC channel (and optionally also an DAC channel). The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(
        self,
        name: str,
        instrument: QickAdcChannel,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instrument=instrument,
            get_parser=instrument.reg2hz,
            set_parser=instrument.hz2reg,
            vals=Numbers(),
            unit="Hz",
            **kwargs,
        )


class DacDegParameter(ManualParameter):
    """Phase parameter with automatic rounding to a multiple of the phase unit of the specified DAC channel. The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(
        self,
        name: str,
        instrument: QickDacChannel,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instrument=instrument,
            get_parser=instrument.reg2deg,
            set_parser=instrument.deg2reg,
            vals=Numbers(),
            unit="deg",
            **kwargs,
        )


class DacSecParameter(ManualParameter):
    """Time parameter with automatic rounding to a multiple of the clock period of the specified DAC channel. The `get_raw()` method returns the time in the number of clock cycles (int)."""

    def __init__(
        self,
        name: str,
        instrument: QickDacChannel,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instrument=instrument,
            get_parser=instrument.cycles2sec,
            set_parser=instrument.sec2cycles,
            vals=Numbers(),
            unit="sec",
            **kwargs,
        )


class AdcSecParameter(ManualParameter):
    """Time parameter with automatic rounding to a multiple of the clock period of the specified ADC channel. The `get_raw()` method returns the time in the number of clock cycles (int)."""

    def __init__(
        self,
        name: str,
        instrument: QickAdcChannel,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instrument=instrument,
            get_parser=instrument.cycles2sec,
            set_parser=instrument.sec2cycles,
            vals=Numbers(),
            unit="sec",
            **kwargs,
        )
