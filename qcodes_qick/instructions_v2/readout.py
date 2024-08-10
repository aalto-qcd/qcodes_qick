from qcodes import ManualParameter, Parameter
from qcodes.validators import Bool, Numbers

from qcodes_qick.channels_v2 import AdcChannel
from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.protocol_base_v2 import HardwareSweep, SweepProgram
from qcodes_qick.validators import MaybeSweep


class Readout(QickInstruction):
    """Generate a specified pulse and trigger an ADC channel.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    pulse : QickInstruction
        The pulse to generate.
    adc : AdcChannel
        The ADC channel to trigger.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    def __init__(
        self,
        parent: QickInstrument,
        pulse: QickInstruction,
        adc: AdcChannel,
        name="Readout",
        **kwargs,
    ):
        super().__init__(parent, dacs=pulse.dacs, adcs=[adc], name=name, **kwargs)
        # assert len(self.dacs) == 1
        assert self.dacs[0].matching_adc.get() == self.adcs[0].channel_num
        assert self.adcs[0].matching_dac.get() == self.dacs[0].channel_num
        self.pulse = pulse

        self.pulse_name = Parameter(
            name="pulse_name",
            instrument=self,
            label="Name of the readout pulse",
            initial_cache_value=self.pulse.full_name,
        )
        self.wait_before = ManualParameter(
            name="wait_before",
            instrument=self,
            label="Wait time before the pulse",
            unit="sec",
            vals=MaybeSweep(Numbers(min_value=0)),
            initial_value=100e-9,
        )
        self.wait_after = ManualParameter(
            name="wait_after",
            instrument=self,
            label="Wait time after the pulse",
            unit="sec",
            vals=MaybeSweep(Numbers(min_value=0)),
            initial_value=100e-9,
        )
        self.adc_trig_offset = ManualParameter(
            name="adc_trig_offset",
            instrument=self,
            label="Delay between the start of the pulse and the ADC trigger",
            unit="sec",
            vals=MaybeSweep(Numbers(min_value=0)),
            initial_value=0,
        )
        self.wait_for_adc = ManualParameter(
            name="wait_for_adc",
            instrument=self,
            label="Pause tProc execution until the end of the ADC readout window",
            vals=Bool(),
            initial_value=True,
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        self.pulse.initialize(program)

    def play(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.delay_auto(self.wait_before.get() * 1e6, gens=True, ros=False)
        program.trigger(
            ros=[self.adcs[0].channel_num],
            t=self.adc_trig_offset.get() * 1e6,
        )
        self.pulse.play(program)
        if self.wait_for_adc.get():
            program.wait_auto(gens=False, ros=True)
        program.delay_auto(t=self.wait_after.get() * 1e6, gens=True, ros=False)

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        """Add a sweep over one of my parameters to a program.

        Parameters
        ----------
        program : SweepProgram
        sweep: HardwareSweep

        """
        raise NotImplementedError(
            f"cannot perform a hardware sweep over {sweep.parameter.name}"
        )
