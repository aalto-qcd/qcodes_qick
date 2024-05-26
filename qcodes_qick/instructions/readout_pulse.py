from qick.averager_program import QickSweep

from qcodes_qick.channels import AdcChannel, DacChannel
from qcodes_qick.instruction_base import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters import (
    GainParameter,
    HzParameter,
    SecParameter,
    TProcSecParameter,
)
from qcodes_qick.protocol_base import HardwareSweep, SweepProgram


class ReadoutPulse(QickInstruction):
    """Generate a rectangular pulse and trigger an ADC channel.

    Parameters
    ----------
    parent : QickInstrument
        Make me a submodule of this QickInstrument.
    dac : DacChannel
        The DAC channel to use.
    adc : AdcChannel
        The ADC channel to use.
    name : str
        My unique name.
    **kwargs : dict, optional
        Keyword arguments to pass on to InstrumentBase.__init__.
    """

    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        adc: AdcChannel,
        name="ReadoutPulse",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        dac.matching_adc.set(adc.channel_num)
        adc.matching_dac.set(dac.channel_num)
        self.dacs = [dac]
        self.adcs = [adc]

        self.gain = GainParameter(
            name="gain",
            instrument=self,
            label="Pulse gain",
            initial_value=0.5,
        )
        self.freq = HzParameter(
            name="freq",
            instrument=self,
            label="Pulse frequency",
            initial_value=1e9,
            channel=self.dacs[0],
        )
        self.length = SecParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            initial_value=10e-6,
            channel=self.dacs[0],
        )
        self.wait_before = TProcSecParameter(
            name="wait_before",
            instrument=self,
            label="Wait time before the pulse",
            initial_value=100e-9,
            qick_instrument=self.parent,
        )
        self.wait_after = TProcSecParameter(
            name="wait_after",
            instrument=self,
            label="Wait time after the pulse",
            initial_value=1e-3,
            qick_instrument=self.parent,
        )
        self.adc_trig_offset = TProcSecParameter(
            name="adc_trig_offset",
            instrument=self,
            label="Delay between the start of the pulse and the ADC trigger",
            initial_value=0,
            qick_instrument=self.parent,
        )
        self.adc_length = SecParameter(
            name="adc_length",
            instrument=self,
            label="Length of the ADC acquisition window",
            initial_value=10e-6,
            channel=self.adcs[0],
        )

    def initialize(self, program: SweepProgram):
        """Add initialization commands to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        program.set_pulse_registers(
            ch=self.dacs[0].channel_num,
            style="const",
            freq=self.freq.get_raw(),
            phase=0,
            gain=self.gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=self.length.get_raw(),
        )
        program.declare_readout(
            ch=self.adcs[0].channel_num,
            length=self.adc_length.get_raw(),
            freq=self.freq.get() / 1e6,
        )
        self.wait_before_reg = program.new_gen_reg(
            gen_ch=self.dacs[0].channel_num,
            init_val=self.wait_before.get() * 1e6,
            reg_type="time",
            tproc_reg=True,
        )

    def play(self, program: SweepProgram, wait_for_adc: bool):
        """Append me to a program.

        Parameters
        ----------
        program : SweepProgram
        """
        assert self in program.protocol.instructions
        program.sync_all()
        program.sync(self.wait_before_reg.page, self.wait_before_reg.addr)
        program.measure(
            adcs=[self.adcs[0].channel_num],
            pulse_ch=self.dacs[0].channel_num,
            adc_trig_offset=self.adc_trig_offset.get_raw(),
            t="auto",
            wait=wait_for_adc,
        )
        program.sync_all(t=self.wait_after.get_raw())

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        """Add a sweep over one of my parameters to a program.

        Parameters
        ----------
        program : SweepProgram
        sweep: HardwareSweep

        """
        if sweep.parameter is self.gain:
            reg = program.get_gen_reg(self.dacs[0].channel_num, "gain")
            program.add_sweep(
                QickSweep(program, reg, sweep.start_int, sweep.stop_int, sweep.num)
            )
        elif sweep.parameter is self.wait_before:
            reg = self.wait_before_reg
            program.add_sweep(
                QickSweep(program, reg, sweep.start * 1e6, sweep.stop * 1e6, sweep.num)
            )
        else:
            raise NotImplementedError(f"cannot sweep over {sweep.parameter.name}")
