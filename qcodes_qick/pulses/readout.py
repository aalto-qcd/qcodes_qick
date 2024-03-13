from typing import Any

from qcodes_qick.channels import AdcChannel, DacChannel
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters import (
    GainParameter,
    HzParameter,
    SecParameter,
    TProcSecParameter,
)
from qcodes_qick.protocol_base import HardwareSweep, SweepProgram
from qcodes_qick.pulse_base import QickPulse
from qick.asm_v1 import AcquireProgram
from qick.averager_program import QickSweep


class ReadoutPulse(QickPulse):
    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        adc: AdcChannel,
        name="ReadoutPulse",
        **kwargs: Any
    ):
        super().__init__(parent, name, **kwargs)
        dac.matching_adc.set(adc.channel)
        adc.matching_dac.set(dac.channel)
        self.dacs = {dac}
        self.adcs = {adc}
        self.dac = dac
        self.adc = adc

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
            channel=self.dac,
        )
        self.length = SecParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            initial_value=10e-6,
            channel=self.dac,
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
            channel=self.adc,
        )

    def initialize(self, program: AcquireProgram):
        program.set_pulse_registers(
            ch=self.dac.channel,
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
            ch=self.adc.channel,
            length=self.adc_length.get_raw(),
            freq=self.freq.get() / 1e6,
        )

    def play(self, program: AcquireProgram, wait_for_adc: bool):
        program.sync_all(t=self.wait_before.get_raw())
        program.measure(
            adcs=[self.adc.channel],
            pulse_ch=self.dac.channel,
            adc_trig_offset=self.adc_trig_offset.get_raw(),
            t="auto",
            wait=wait_for_adc,
        )
        program.sync_all(t=self.wait_after.get_raw())

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        if sweep.parameter is self.gain:
            reg = program.get_gen_reg(self.dac.channel, "gain")
            program.add_sweep(
                QickSweep(program, reg, sweep.start_int, sweep.stop_int, sweep.num)
            )
        else:
            raise NotImplementedError
