from __future__ import annotations

from typing import TYPE_CHECKING

from qcodes import InstrumentChannel, ManualParameter, Parameter
from qcodes.utils.validators import Enum, Numbers

if TYPE_CHECKING:
    from qick.asm_v2 import QickProgramV2

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
            label="Channel number of the ADC to match the frequency unit to.",
            vals=Enum(None, *range(len(self.parent.soccfg["readouts"]))),
            initial_value=None,
        )
        self.nqz = ManualParameter(
            name="nqz",
            instrument=self,
            label="Nyquist zone",
            vals=Enum(1, 2),
            initial_value=1,
        )
        self.digital_mixer_freq = ManualParameter(
            name="digital_mixer_freq",
            instrument=self,
            label="LO frequency of the digital mixer. Only used for an interpolated or muxed generator.",
            unit="Hz",
            vals=Numbers(),
            initial_value=0,
        )

    def initialize(self, program: QickProgramV2):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : AbsQickProgram
        """
        if self.type.get() in ["axis_sg_int4_v2"]:
            # this is an interpolated or muxed generator
            mixer_freq = self.digital_mixer_freq.get() / 1e6
        else:
            assert self.digital_mixer_freq.get() == 0
            mixer_freq = None
        program.declare_gen(self.channel_num, self.nqz.get(), mixer_freq)


class AdcChannel(InstrumentChannel):
    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, channel_num: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.channel_num = channel_num
        config = parent.soccfg["readouts"][channel_num]

        self.type = Parameter(
            name="type",
            instrument=self,
            label="ADC type",
            initial_cache_value=config["ro_type"],
        )
        self.f_fabric = Parameter(
            name="f_fabric",
            instrument=self,
            label="Fabric clock frequency",
            initial_cache_value=config["f_fabric"] * 1e6,
        )
        self.avgbuf_fullpath = Parameter(
            name="avgbuf_fullpath",
            instrument=self,
            label="Full path (in the firmware) of the average buffer driven by this channel",
            initial_cache_value=config["avgbuf_fullpath"],
        )
        self.matching_dac = ManualParameter(
            name="matching_dac",
            instrument=self,
            label="Channel number of the DAC to match the frequency unit to.",
            vals=Enum(None, *range(len(self.parent.soccfg["gens"]))),
            initial_value=None,
        )
        self.freq = ManualParameter(
            name="freq",
            instrument=self,
            label="LO frequency for digital downconversion",
            unit="Hz",
            vals=Numbers(),
            initial_value=0,
        )
        self.length = ManualParameter(
            name="length",
            instrument=self,
            label="Readout window length",
            unit="sec",
            vals=Numbers(min_value=0),
            initial_value=10e-6,
        )

    def initialize(self, program: QickProgramV2):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : AbsQickProgram
        """
        if self.type.get() in ["axis_readout_v3", "axis_dyn_readout_v1"]:
            # this is a tProc-configured readout
            program.declare_readout(
                ch=self.channel_num,
                length=self.length.get() * 1e6,
            )
            program.add_readoutconfig(
                ch=self.channel_num,
                name=self.name,
                freq=self.freq.get() / 1e6,
                phase=0,
                gen_ch=self.matching_dac.get(),
            )
            program.send_readoutconfig(
                ch=self.channel_num,
                name=self.name,
            )
        else:
            # this is a PYNQ-configured readout
            program.declare_readout(
                ch=self.channel_num,
                freq=self.freq.get() / 1e6,
                phase=0,
                length=self.length.get() * 1e6,
                gen_ch=self.matching_dac.get(),
            )
