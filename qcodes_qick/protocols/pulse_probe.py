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


class PulseProbeProtocol(SweepProtocol):

    def __init__(
        self,
        parent: QickInstrument,
        qubit_dac: DacChannel,
        readout_dac: DacChannel,
        readout_adc: AdcChannel,
        name="PulseProbeProtocol",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.qubit_dac = qubit_dac
        self.readout_dac = readout_dac
        self.readout_adc = readout_adc
        self.readout_dac.matching_adc.set(readout_adc.channel)
        self.readout_adc.matching_dac.set(readout_dac.channel)

        self.qubit_gain = GainParameter(
            name="qubit_gain",
            instrument=self,
            label="Gain of qubit pulse",
            initial_value=0.5,
        )

        self.qubit_freq = HzParameter(
            name="qubit_freq",
            instrument=self,
            label="Frequency of qubit pulse",
            initial_value=4e9,
            channel=qubit_dac,
        )

        self.qubit_length = SecParameter(
            name="qubit_length",
            instrument=self,
            label="Length of qubit pulse",
            initial_value=10e-6,
            channel=qubit_dac,
        )

        self.qubit_readout_gap = TProcSecParameter(
            name="qubit_readout_gap",
            instrument=self,
            label="Gap between qubit pulse and readout pulse",
            initial_value=50e-9,
            qick_instrument=self.parent,
        )

        self.readout_gain = GainParameter(
            name="readout_gain",
            instrument=self,
            label="Gain of readout pulse",
            initial_value=0.5,
        )

        self.readout_freq = HzParameter(
            name="readout_freq",
            instrument=self,
            label="Frequency of readout pulse",
            initial_value=6e9,
            channel=self.readout_dac,
        )

        self.readout_length = SecParameter(
            name="readout_length",
            instrument=self,
            label="Length of readout pulse",
            initial_value=10e-6,
            channel=self.readout_dac,
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

    def generate_program(
        self, soccfg: QickConfig, hardware_sweeps: Sequence[HardwareSweep] = ()
    ):
        return PulseProbeProgram(soccfg, self, hardware_sweeps)


class PulseProbeProgram(SweepProgram):

    protocol: PulseProbeProtocol

    def initialize(self):
        self.declare_gen(
            ch=self.protocol.qubit_dac.channel,
            nqz=self.protocol.qubit_dac.nqz.get(),
        )
        self.declare_gen(
            ch=self.protocol.readout_dac.channel,
            nqz=self.protocol.readout_dac.nqz.get(),
        )
        self.declare_readout(
            ch=self.protocol.readout_adc.channel,
            length=self.protocol.readout_length.get_raw(),
            sel="product",
            freq=self.protocol.readout_freq.get() / 1e6,
        )
        self.set_pulse_registers(
            ch=self.protocol.qubit_dac.channel,
            style="const",
            freq=self.protocol.qubit_freq.get_raw(),
            phase=0,
            gain=self.protocol.qubit_gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=self.protocol.qubit_length.get_raw(),
        )
        self.set_pulse_registers(
            ch=self.protocol.readout_dac.channel,
            style="const",
            freq=self.protocol.readout_freq.get_raw(),
            phase=0,
            gain=self.protocol.readout_gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=self.protocol.readout_length.get_raw(),
        )

        for sweep in reversed(self.hardware_sweeps):
            if sweep.parameter is self.protocol.qubit_gain:
                reg = self.get_gen_reg(self.protocol.qubit_dac.channel, "gain")
                self.add_sweep(
                    QickSweep(self, reg, sweep.start_int, sweep.stop_int, sweep.num)
                )
            elif sweep.parameter is self.protocol.qubit_freq:
                reg = self.get_gen_reg(self.protocol.qubit_dac.channel, "freq")
                self.add_sweep(
                    QickSweep(self, reg, sweep.start / 1e6, sweep.stop / 1e6, sweep.num)
                )
            elif sweep.parameter is self.protocol.readout_gain:
                reg = self.get_gen_reg(self.protocol.readout_dac.channel, "gain")
                self.add_sweep(
                    QickSweep(self, reg, sweep.start_int, sweep.stop_int, sweep.num)
                )
            else:
                raise NotImplementedError

        self.synci(200)  # Give processor some time to configure pulses

    def body(self):
        self.pulse(ch=self.protocol.qubit_dac.channel, t="auto")
        self.sync_all(t=self.protocol.qubit_readout_gap.get_raw())
        self.measure(
            adcs=[self.protocol.readout_adc.channel],
            pulse_ch=self.protocol.readout_dac.channel,
            adc_trig_offset=self.protocol.adc_trig_offset.get_raw(),
            t="auto",
            wait=True,
            syncdelay=self.protocol.relax_delay.get_raw(),
        )
