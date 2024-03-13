from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qcodes_qick.channels import AdcChannel, DacChannel
from qcodes_qick.parameters import (
    GainParameter,
    HzParameter,
    SecParameter,
    TProcSecParameter,
)
from qcodes_qick.protocol_base import HardwareSweep, SweepProgram, SweepProtocol
from qick.averager_program import QickSweep
from qick.qick_asm import QickConfig

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class S21Protocol(SweepProtocol):

    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        adc: AdcChannel,
        name="S21Protocol",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.dac = dac
        self.adc = adc
        self.dac.matching_adc.set(adc.channel)
        self.adc.matching_dac.set(dac.channel)

        self.pulse_gain = GainParameter(
            name="pulse_gain",
            instrument=self,
            label="Pulse gain",
            initial_value=0.5,
        )

        self.pulse_freq = HzParameter(
            name="pulse_freq",
            instrument=self,
            label="Pulse frequency",
            initial_value=1e9,
            channel=self.dac,
        )

        self.pulse_length = SecParameter(
            name="pulse_length",
            instrument=self,
            label="Pulse length",
            initial_value=10e-6,
            channel=self.dac,
        )

        self.adc_trig_offset = TProcSecParameter(
            name="adc_trig_offset",
            instrument=self,
            label="Delay between sending probe pulse and ADC initialization",
            initial_value=0,
            qick_instrument=self.parent,
        )

        self.relax_delay = TProcSecParameter(
            name="relax_delay",
            instrument=self,
            label="Delay between reps",
            initial_value=1e-3,
            qick_instrument=self.parent,
        )

        self.adc_length = SecParameter(
            name="adc_length",
            instrument=self,
            label="Length of ADC acquisition window",
            initial_value=10e-6,
            channel=self.adc,
        )

    def generate_program(
        self, soccfg: QickConfig, hardware_sweeps: Sequence[HardwareSweep] = ()
    ):
        return S21Program(soccfg, self, hardware_sweeps)


class S21Program(SweepProgram):

    protocol: S21Protocol

    def initialize(self):
        self.declare_gen(
            ch=self.protocol.dac.channel,
            nqz=self.protocol.dac.nqz.get(),
        )
        self.declare_readout(
            ch=self.protocol.adc.channel,
            length=self.protocol.adc_length.get_raw(),
            sel="product",
            freq=self.protocol.pulse_freq.get() / 1e6,
        )
        self.set_pulse_registers(
            ch=self.protocol.dac.channel,
            style="const",
            freq=self.protocol.pulse_freq.get_raw(),
            phase=0,
            gain=self.protocol.pulse_gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=self.protocol.pulse_length.get_raw(),
        )

        for sweep in reversed(self.hardware_sweeps):
            if sweep.parameter is self.protocol.pulse_gain:
                reg = self.get_gen_reg(self.protocol.dac.channel, "gain")
                self.add_sweep(
                    QickSweep(self, reg, sweep.start_int, sweep.stop_int, sweep.num)
                )
            else:
                raise NotImplementedError

        self.synci(200)  # Give processor some time to configure pulses

    def body(self):
        self.measure(
            adcs=[self.protocol.adc.channel],
            pulse_ch=self.protocol.dac.channel,
            adc_trig_offset=self.protocol.adc_trig_offset.get_raw(),
            t="auto",
            wait=True,
            syncdelay=self.protocol.relax_delay.get_raw(),
        )
