from typing import Any, Union

from qcodes.parameters import ManualParameter, Parameter
from qcodes.validators import Ints, Sequence as SequenceValidator
from qick.asm_v2 import QickSweep

from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.muxed_dac import MuxedDacChannel
from qcodes_qick.parameters import SecParameter
from qcodes_qick.protocol_base_v2 import HardwareSweep, SweepProgram


class MuxedConstantPulse(QickInstruction):
    def __init__(
        self,
        parent: QickInstrument,
        dac: MuxedDacChannel,
        name="MuxedConstantPulse",
        **kwargs: Any,
    ):
        """
        Parameters
        ----------
        parent : QickInstrument
            Make me a submodule of this QickInstrument.
        dac : MuxedDacChannel
            The DAC channel to use.
        name : str
            My unique name.
        **kwargs : dict, optional
            Keyword arguments to pass on to InstrumentBase.__init__.
        """
        super().__init__(parent, name, **kwargs)
        assert isinstance(dac, MuxedDacChannel)
        self.dacs = [dac]

        self.dac_channel_num = Parameter(
            name="dac_channel_num",
            instrument=self,
            label="DAC channel number",
            initial_cache_value=dac.channel_num,
        )
        self.length = SecParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            initial_value=10e-6,
            channel=self.dacs[0],
        )
        self.tone_nums = ManualParameter(
            name="tone_nums",
            instrument=self,
            label="List of tone numbers to generate",
            initial_value=[0],
            vals=SequenceValidator(Ints(0, len(self.dacs[0].tones) - 1)),
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        program.add_pulse(
            ch=self.dacs[0].channel_num,
            name=self.full_name,
            style="const",
            mask=self.tone_nums.get(),
            length=self.length.get() * 1e6,
        )

    def play(self, program: SweepProgram, t: Union[float, QickSweep, str] = "auto"):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        t : float, QickSweep, or "auto"
            Time in seconds. "auto" means the end of the last pulse on the DAC channel.
        """
        if not isinstance(t, str):
            t *= 1e6
        program.pulse(self.dacs[0].channel_num, self.full_name, t)

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        """Add a sweep over one of my parameters to a program.

        Parameters
        ----------
        program : SweepProgram
        sweep: HardwareSweep
        """
        raise NotImplementedError(f"cannot sweep over {sweep.parameter.name}")
