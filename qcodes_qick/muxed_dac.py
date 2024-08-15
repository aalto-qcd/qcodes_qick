from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import ChannelTuple, InstrumentChannel, ManualParameter
from qcodes.validators import Numbers

from qcodes_qick.channels_v2 import DacChannel

if TYPE_CHECKING:
    from qick.qick_asm import AbsQickProgram

    from qcodes_qick.instruments import QickInstrument


class MuxedDacTone(InstrumentChannel):
    parent: MuxedDacChannel

    def __init__(self, parent: MuxedDacChannel, name: str, **kwargs):
        super().__init__(parent, name, **kwargs)

        self.freq = ManualParameter(
            name="freq",
            instrument=self,
            label="Frequency of the tone",
            unit="Hz",
            vals=Numbers(),
            initial_value=0,
        )
        self.gain = ManualParameter(
            name="gain",
            instrument=self,
            label="Gain of the tone",
            unit="DAC unit",
            vals=Numbers(-1, 1),
            initial_value=0.5,
        )


class MuxedDacChannel(DacChannel):
    def __init__(self, parent: QickInstrument, name: str, channel_num: int, **kwargs):
        super().__init__(parent, name, channel_num, **kwargs)

        self.tones = ChannelTuple(
            parent=self,
            name="tones",
            chan_type=MuxedDacTone,
            chan_list=[
                MuxedDacTone(self, f"tone{i}")
                for i in range(parent.soccfg["gens"][channel_num]["n_tones"])
            ],
        )

    def initialize(self, program: AbsQickProgram):
        program.declare_gen(
            ch=self.channel_num,
            nqz=self.nqz.get(),
            mux_freqs=[tone.freq.get() / 1e6 for tone in self.tones],
            mux_gains=[tone.gain.get() for tone in self.tones],
            ro_ch=self.matching_adc.get(),
        )
