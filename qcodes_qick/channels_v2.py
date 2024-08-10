from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import InstrumentChannel, ManualParameter, Parameter
from qcodes.utils.validators import Ints, Numbers

from qcodes_qick.validators import MaybeSweep

if TYPE_CHECKING:
    from qick.qick_asm import AbsQickProgram

    from qcodes_qick.instruments import QickInstrument


class DacChannel(InstrumentChannel):
    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, channel_num: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.channel_num = channel_num

        self.type = Parameter(
            name="type",
            instrument=self,
            label="DAC type",
            initial_cache_value=parent.soccfg["gens"][channel_num]["type"],
        )
        self.matching_adc = ManualParameter(
            name="matching_adc",
            instrument=self,
            label="Channel number of the ADC to match the frequency unit to. -1 means don't perform any matching.",
            vals=Ints(-1, len(self.parent.soccfg["readouts"]) - 1),
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
        """Add initialization commands to a program.

        Parameters
        ----------
        program : AbsQickProgram
        """
        program.declare_gen(ch=self.channel_num, nqz=self.nqz.get())


class AdcChannel(InstrumentChannel):
    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, channel_num: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.channel_num = channel_num

        self.matching_dac = ManualParameter(
            name="matching_dac",
            instrument=self,
            label="Channel number of the DAC to match the frequency unit to. -1 means don't perform any matching.",
            vals=Ints(-1, len(self.parent.soccfg["gens"]) - 1),
            initial_value=-1,
        )
        self.freq = ManualParameter(
            name="freq",
            instrument=self,
            label="LO frequency for digital downconversion",
            unit="Hz",
            vals=MaybeSweep(Numbers()),
            initial_value=0,
        )
        self.length = ManualParameter(
            name="length",
            instrument=self,
            label="Readout window length",
            unit="sec",
            vals=MaybeSweep(Numbers(min_value=0)),
            initial_value=10e-6,
        )

    def initialize(self, program: AbsQickProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : AbsQickProgram
        """
        # if self.matching_dac.get() == -1:
        #     gen_ch = None
        # else:
        #     gen_ch = self.matching_dac.get()
        program.declare_readout(
            ch=self.channel_num,
            freq=self.freq.get() / 1e6,
            phase=0,
            length=self.length.get() * 1e6,
            # gen_ch=gen_ch,  # Don't know why, but uncommenting this line makes the phase of the readout signal depend on the time of the readout
        )
