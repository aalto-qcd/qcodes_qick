from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import ChannelTuple, InstrumentChannel
from qick.qick_asm import AbsQickProgram

from qcodes_qick.channels import DacChannel
from qcodes_qick.parameters import GainParameter, HzParameter

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class MuxedDacTone(InstrumentChannel):
    parent: MuxedDacChannel

    def __init__(self, parent: MuxedDacChannel, name: str, **kwargs):
        super().__init__(parent, name, **kwargs)

        self.freq = HzParameter(
            name="freq",
            instrument=self,
            label="Frequency of the tone",
            initial_value=1e9,
            channel=parent,
        )

        self.gain = GainParameter(
            name="gain",
            instrument=self,
            label="Gain of the tone",
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
        )
