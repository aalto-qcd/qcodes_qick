from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import InstrumentChannel, ManualParameter, Parameter
from qcodes.utils.validators import Ints
from qick.qick_asm import AbsQickProgram

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class DacChannel(InstrumentChannel):
    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.channel = channel

        self.type = Parameter(
            name="type",
            instrument=self,
            label="Generator type",
            initial_cache_value=parent.soccfg["gens"][channel]["type"],
        )

        self.matching_adc = ManualParameter(
            name="matching_adc",
            instrument=self,
            label="Channel number of the ADC to match the frequency unit to. -1 means don't perform any matching.",
            vals=Ints(-1, len(self.parent.soccfg["gens"]) - 1),
            initial_value=-1,
        )
        self.nqz = ManualParameter(
            name="nqz",
            instrument=self,
            label="Nyquist zone",
            vals=Ints(1, 2),
            initial_value=1,
        )

    def initialize(self, program: AbsQickProgram):
        program.declare_gen(ch=self.channel, nqz=self.nqz.get())

    def reg2hz(self, reg: int) -> float:
        """Convert a DAC frequency from the register value (int) to Hz"""
        return self.parent.soccfg.reg2freq(reg, self.channel) * 1e6

    def hz2reg(self, hz: float) -> int:
        """Convert a DAC frequency from Hz to the register value (int)"""
        adc_channel = self.matching_adc.get()
        if adc_channel == -1:
            adc_channel = None
        return self.parent.soccfg.freq2reg(hz / 1e6, self.channel, adc_channel)

    def reg2deg(self, reg: int) -> float:
        """Convert a DAC phase from the register value (int) to degrees"""
        return self.parent.soccfg.reg2deg(reg, self.channel)

    def deg2reg(self, deg: float) -> int:
        """Convert a DAC phase from degrees to the register value (int)"""
        return self.parent.soccfg.deg2reg(deg, self.channel)

    def cycles2sec(self, reg: int) -> float:
        """Convert time from the number of DAC clock cycles to seconds"""
        return self.parent.soccfg.cycles2us(reg, gen_ch=self.channel) / 1e6

    def sec2cycles(self, sec: float) -> int:
        """Convert time from seconds to the number of DAC clock cycles"""
        return self.parent.soccfg.us2cycles(sec * 1e6, gen_ch=self.channel)


class AdcChannel(InstrumentChannel):
    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.channel = channel

        self.matching_dac = ManualParameter(
            name="matching_dac",
            instrument=self,
            label="Channel number of the DAC to match the frequency unit to. -1 means don't perform any matching.",
            vals=Ints(-1, len(self.parent.soccfg["readouts"]) - 1),
            initial_value=-1,
        )

    def reg2hz(self, reg: int) -> float:
        """Convert ADC frequency from the register value (int) to Hz"""
        return self.parent.soccfg.reg2freq_adc(reg, self.channel) * 1e6

    def hz2reg(self, hz: float) -> int:
        """Convert ADC frequency from Hz to the register value (int)"""
        dac_channel = self.matching_dac.get()
        if dac_channel == -1:
            dac_channel = None
        return self.parent.soccfg.freq2reg_adc(hz / 1e6, self.channel, dac_channel)

    def cycles2sec(self, reg: int) -> float:
        """Convert time from the number of ADC clock cycles to seconds"""
        return self.parent.soccfg.cycles2us(reg, ro_ch=self.channel) / 1e6

    def sec2cycles(self, sec: float) -> int:
        """Convert time from seconds to the number of ADC clock cycles"""
        return self.parent.soccfg.us2cycles(sec * 1e6, ro_ch=self.channel)
