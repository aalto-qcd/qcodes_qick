from typing import Sequence

from qcodes import Parameter

from qcodes_qick.channels_v2 import AdcChannel
from qcodes_qick.instruction_base_v2 import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters_v2 import SweepableNumbers, SweepableParameter
from qcodes_qick.protocol_base_v2 import SweepProgram


class Readout(QickInstruction):
    """Generate a specified pulse and trigger the specified ADC channels.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    pulse : QickInstruction
        The pulse to generate.
    adc : Sequence[AdcChannel]
        The ADC channels to trigger.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    def __init__(
        self,
        parent: QickInstrument,
        pulse: QickInstruction,
        adcs: Sequence[AdcChannel],
        name="Readout",
        **kwargs,
    ):
        super().__init__(parent, dacs=pulse.dacs, adcs=adcs, name=name, **kwargs)
        # assert len(self.dacs) == 1
        # assert self.dacs[0].matching_adc.get() == self.adcs[0].channel_num
        # assert self.adcs[0].matching_dac.get() == self.dacs[0].channel_num
        self.pulse = pulse

        self.pulse_name = Parameter(
            name="pulse_name",
            instrument=self,
            label="Name of the readout pulse",
            initial_cache_value=self.pulse.full_name,
        )
        self.wait_before = SweepableParameter(
            name="wait_before",
            instrument=self,
            label="Wait time before the pulse",
            unit="sec",
            vals=SweepableNumbers(min_value=0),
            initial_value=100e-9,
        )
        self.wait_after = SweepableParameter(
            name="wait_after",
            instrument=self,
            label="Wait time after the pulse",
            unit="sec",
            vals=SweepableNumbers(min_value=0),
            initial_value=100e-9,
        )
        self.adc_trig_offset = SweepableParameter(
            name="adc_trig_offset",
            instrument=self,
            label="Delay between the start of the pulse and the ADC trigger",
            unit="sec",
            vals=SweepableNumbers(min_value=0),
            initial_value=0,
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        self.pulse.initialize(program)

    def append_to(self, program: SweepProgram):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.delay_auto(self.wait_before.get() * 1e6, gens=True, ros=False)
        program.trigger(
            ros=[adc.channel_num for adc in self.adcs],
            t=self.adc_trig_offset.get() * 1e6,
        )
        self.pulse.append_to(program)
        program.delay_auto(t=self.wait_after.get() * 1e6, gens=True, ros=False)
