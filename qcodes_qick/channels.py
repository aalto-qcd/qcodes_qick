from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import InstrumentChannel, ManualParameter
from qcodes.utils.validators import Ints, Numbers

from qcodes_qick.parameters import DacDegParameter, DacHzParameter, DacSecParameter

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class QickDacChannel(InstrumentChannel):

    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.channel = channel

        self.matching_adc = ManualParameter(
            name="matching_adc",
            instrument=self,
            label="Channel number of the ADC to match the frequency unit to. -1 means don't perform any matching.",
            vals=Ints(-1, self.parent.adc_count - 1),
            initial_value=-1,
        )

        self.nqz = ManualParameter(
            name="nqz",
            instrument=self,
            label="Nyquist zone",
            vals=Ints(1, 2),
            initial_value=1,
        )

        self.pulse_gain = ManualParameter(
            name="pulse_gain",
            instrument=self,
            label="DAC gain",
            vals=Ints(-32768, 32767),
            unit="DAC units",
            initial_value=10000,
        )

        self.pulse_freq = DacHzParameter(
            name="pulse_freq",
            instrument=self,
            label="NCO frequency",
            initial_value=1e9,
        )

        self.pulse_phase = DacDegParameter(
            name="pulse_phase",
            instrument=self,
            label="Pulse phase",
            initial_value=0,
        )

        self.pulse_length = DacSecParameter(
            name="pulse_length",
            instrument=self,
            label="Pulse length",
            initial_value=10e-6,
        )

    def reg2hz(self, reg: int) -> float:
        return self.parent.soccfg.reg2freq(reg, self.channel) * 1e6

    def hz2reg(self, hz: float) -> int:
        adc_channel = self.matching_adc.get()
        if adc_channel == -1:
            adc_channel = None
        return self.parent.soccfg.freq2reg(hz / 1e6, self.channel, adc_channel)

    def reg2deg(self, reg: int) -> float:
        return self.parent.soccfg.reg2deg(reg, self.channel)

    def deg2reg(self, deg: float) -> int:
        return self.parent.soccfg.deg2reg(deg, self.channel)

    def cycles2sec(self, reg: int) -> float:
        return self.parent.soccfg.cycles2us(reg, gen_ch=self.channel) / 1e6

    def sec2cycles(self, sec: float) -> int:
        return self.parent.soccfg.us2cycles(sec * 1e6, gen_ch=self.channel)


class QickAdcChannel(InstrumentChannel):

    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.channel = channel

        self.matching_dac = ManualParameter(
            name="matching_dac",
            instrument=self,
            label="Channel number of the DAC to match the frequency unit to. -1 means don't perform any matching.",
            vals=Ints(-1, self.parent.dac_count - 1),
            initial_value=-1,
        )

        self.readout_time = ManualParameter(
            name="readout_time",
            instrument=self,
            label="Up time of the ADC readout | Used for timetrace applications",
            vals=Numbers(0, 1000000),
            unit="Clock ticks",
            initial_value=0,
        )

    def reg2hz(self, reg: int) -> float:
        return self.parent.soccfg.reg2freq_adc(reg, self.channel) * 1e6

    def hz2reg(self, hz: float) -> int:
        dac_channel = self.matching_dac.get()
        if dac_channel == -1:
            dac_channel = None
        return self.parent.soccfg.freq2reg_adc(hz / 1e6, self.channel, dac_channel)

    def cycles2sec(self, reg: int) -> float:
        return self.parent.soccfg.cycles2us(reg, ro_ch=self.channel) / 1e6

    def sec2cycles(self, sec: float) -> int:
        return self.parent.soccfg.us2cycles(sec * 1e6, ro_ch=self.channel)
