from typing import Optional

from qcodes import Parameter
from qcodes.validators import Numbers

from qick.qick_asm import QickConfig


class QickDacFreqParameter(Parameter):
    """Frequency parameter with automatic rounding to a multiple of the frequency unit of the specified DAC channel (and optionally also an ADC channel). The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(
        self,
        name: str,
        soccfg: QickConfig,
        dac_ch: int,
        adc_ch: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            get_parser=lambda reg: soccfg.reg2freq(reg, dac_ch) * 1e6,
            set_parser=lambda freq: soccfg.freq2reg(freq / 1e6, dac_ch, adc_ch),
            vals=Numbers(),
            unit="Hz",
            **kwargs,
        )


class QickAdcFreqParameter(Parameter):
    """Frequency parameter with automatic rounding to a multiple of the frequency unit of the specified ADC channel (and optionally also an DAC channel). The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(
        self,
        name: str,
        soccfg: QickConfig,
        adc_ch: int,
        dac_ch: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            get_parser=lambda reg: soccfg.reg2freq_adc(reg, adc_ch) * 1e6,
            set_parser=lambda freq: soccfg.freq2reg_adc(freq / 1e6, adc_ch, dac_ch),
            vals=Numbers(),
            unit="Hz",
            **kwargs,
        )


class QickDacPhaseParameter(Parameter):
    """Phase parameter with automatic rounding to a multiple of the phase unit of the specified DAC channel. The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(
        self,
        name: str,
        soccfg: QickConfig,
        dac_ch: int,
        **kwargs,
    ):
        super().__init__(
            name=name,
            get_parser=lambda reg: soccfg.reg2deg(reg, dac_ch),
            set_parser=lambda deg: soccfg.deg2reg(deg, dac_ch),
            vals=Numbers(),
            unit="deg",
            **kwargs,
        )


class QickDacTimeParameter(Parameter):
    """Time parameter with automatic rounding to a multiple of the time unit of the specified DAC channel. The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(
        self,
        name: str,
        soccfg: QickConfig,
        dac_ch: int,
        **kwargs,
    ):
        super().__init__(
            name=name,
            get_parser=lambda reg: soccfg.cycles2us(reg, gen_ch=dac_ch) / 1e6,
            set_parser=lambda time: soccfg.us2cycles(time * 1e6, gen_ch=dac_ch),
            vals=Numbers(),
            unit="sec",
            **kwargs,
        )


class QickAdcTimeParameter(Parameter):
    """Time parameter with automatic rounding to a multiple of the time unit of the specified ADC channel. The `get_raw()` method returns the register value (int) that should be sent to QICK."""

    def __init__(
        self,
        name: str,
        soccfg: QickConfig,
        adc_ch: int,
        **kwargs,
    ):
        super().__init__(
            name=name,
            get_parser=lambda reg: soccfg.cycles2us(reg, ro_ch=adc_ch) / 1e6,
            set_parser=lambda time: soccfg.us2cycles(time * 1e6, ro_ch=adc_ch),
            vals=Numbers(),
            unit="sec",
            **kwargs,
        )
