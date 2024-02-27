from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qcodes import Station

from qcodes_qick.channels import AdcChannel, DacChannel
from qcodes_qick.parameters import (
    GainParameter,
    HzParameter,
    SecParameter,
    TProcSecParameter,
)
from qcodes_qick.protocol_base import HardwareSweep, NDAveragerProtocol
from qick.averager_program import NDAveragerProgram, QickSweep

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class PulseProbeProtocol(NDAveragerProtocol):

    def __init__(
        self,
        station: Station,
        parent: QickInstrument,
        qubit_dac: DacChannel,
        readout_dac: DacChannel,
        readout_adc: AdcChannel,
        name="PulseProbeProtocol",
        **kwargs,
    ):
        super().__init__(station, parent, name, PulseProbeProgram, **kwargs)
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


class PulseProbeProgram(NDAveragerProgram):
    """
    This class performs a hardware loop sweep over one or more registers
    in the board. The limit is seven registers.


    Methods
    -------
    initialize(self):
        Initializes the program and defines important variables and registers.
        The sweeps are defined by self.add_sweep calls.
    body(self):
        Defines the structure of the actual measurement and will be looped over reps times.
    """

    def initialize(self):
        p: PulseProbeProtocol = self.cfg["protocol"]
        hardware_sweeps: Sequence[HardwareSweep] = self.cfg.get("hardware_sweeps", ())

        self.declare_gen(
            ch=p.qubit_dac.channel,
            nqz=p.qubit_dac.nqz.get(),
        )
        self.declare_gen(
            ch=p.readout_dac.channel,
            nqz=p.readout_dac.nqz.get(),
        )
        self.declare_readout(
            ch=p.readout_adc.channel,
            length=p.readout_length.get_raw(),
            sel="product",
            freq=p.readout_freq.get() / 1e6,
        )
        self.set_pulse_registers(
            ch=p.qubit_dac.channel,
            style="const",
            freq=p.qubit_freq.get_raw(),
            phase=0,
            gain=p.qubit_gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=p.qubit_length.get_raw(),
        )
        self.set_pulse_registers(
            ch=p.readout_dac.channel,
            style="const",
            freq=p.readout_freq.get_raw(),
            phase=0,
            gain=p.readout_gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=p.readout_length.get_raw(),
        )

        for sweep in reversed(hardware_sweeps):
            if sweep.parameter is p.qubit_gain:
                reg = self.get_gen_reg(p.qubit_dac.channel, "gain")
                self.add_sweep(
                    QickSweep(self, reg, sweep.start_int, sweep.stop_int, sweep.num)
                )
            elif sweep.parameter is p.qubit_freq:
                reg = self.get_gen_reg(p.qubit_dac.channel, "freq")
                self.add_sweep(
                    QickSweep(self, reg, sweep.start / 1e6, sweep.stop / 1e6, sweep.num)
                )
            elif sweep.parameter is p.readout_gain:
                reg = self.get_gen_reg(p.readout_dac.channel, "gain")
                self.add_sweep(
                    QickSweep(self, reg, sweep.start_int, sweep.stop_int, sweep.num)
                )
            else:
                raise NotImplementedError

        self.synci(200)  # Give processor some time to configure pulses

    def body(self):
        p: PulseProbeProtocol = self.cfg["protocol"]

        self.pulse(ch=p.qubit_dac.channel, t="auto")
        self.sync_all(t=p.qubit_readout_gap.get_raw())
        self.measure(
            adcs=[p.readout_adc.channel],
            pulse_ch=p.readout_dac.channel,
            adc_trig_offset=p.adc_trig_offset.get_raw(),
            t="auto",
            wait=True,
            syncdelay=p.relax_delay.get_raw(),
        )
