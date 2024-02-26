from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from qcodes import Station

from qcodes_qick.channels import AdcChannel, DacChannel
from qcodes_qick.parameters import (
    DegParameter,
    GainParameter,
    HzParameter,
    SecParameter,
    TProcSecParameter,
)
from qcodes_qick.protocols import HardwareSweep, NDAveragerProtocol
from qick.asm_v1 import FullSpeedGenManager
from qick.averager_program import NDAveragerProgram, QickSweep

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class S21Protocol(NDAveragerProtocol):

    def __init__(
        self,
        station: Station,
        parent: QickInstrument,
        dac: DacChannel,
        adc: AdcChannel,
        name="S21Protocol",
        **kwargs,
    ):
        super().__init__(station, parent, name, S21Program, **kwargs)
        self.dac = dac
        self.adc = adc
        self.dac.matching_adc.set(adc.channel)
        self.adc.matching_dac.set(dac.channel)

        self.pulse_gain = GainParameter(
            name="pulse_gain",
            instrument=self,
            label="DAC gain",
            initial_value=0.5,
        )

        self.pulse_freq = HzParameter(
            name="pulse_freq",
            instrument=self,
            label="Pulse frequency",
            initial_value=1e9,
            channel=self.dac,
        )

        self.pulse_phase = DegParameter(
            name="pulse_phase",
            instrument=self,
            label="Pulse phase",
            initial_value=0,
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

        self.readout_length = SecParameter(
            name="readout_length",
            instrument=self,
            label="Length of the readout",
            initial_value=10e-6,
            channel=self.adc,
        )


class S21Program(NDAveragerProgram):
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
        p: S21Protocol = self.cfg["protocol"]
        hardware_sweeps: Sequence[HardwareSweep] = self.cfg.get("hardware_sweeps", ())

        self.declare_gen(
            ch=p.dac.channel,
            nqz=p.dac.nqz.get(),
        )
        self.declare_readout(
            ch=p.adc.channel,
            length=p.readout_length.get_raw(),
            sel="product",
            freq=p.pulse_freq.get() / 1e6,
        )
        self.set_pulse_registers(
            ch=p.dac.channel,
            style="const",
            freq=p.pulse_freq.get_raw(),
            phase=p.pulse_phase.get_raw(),
            gain=p.pulse_gain.get_raw(),
            phrst=0,
            stdysel="zero",
            mode="oneshot",
            length=p.pulse_length.get_raw(),
        )

        for sweep in reversed(hardware_sweeps):
            if sweep.parameter is p.pulse_gain:
                reg = self.get_gen_reg(p.dac.channel, "gain")
                self.add_sweep(
                    QickSweep(self, reg, sweep.start_int, sweep.stop_int, sweep.num)
                )
            elif sweep.parameter is p.pulse_freq:
                raise ValueError("readout frequency cannot be swept in hardware")
            elif sweep.parameter is p.pulse_phase:
                raise NotImplementedError
                reg = self.get_gen_reg(p.dac.channel, "phase")
                self.add_sweep(QickSweep(self, reg, sweep.start, sweep.stop, sweep.num))
            elif sweep.parameter is p.pulse_length:
                raise NotImplementedError
            elif sweep.parameter is p.adc_trig_offset:
                raise NotImplementedError
            elif sweep.parameter is p.relax_delay:
                raise NotImplementedError
            elif sweep.parameter is p.readout_length:
                raise NotImplementedError
            else:
                raise NotImplementedError

                # Getting the gen manager for calculating the correct start and end points of the mode register.
                # Thus, by utilizing these methods you may ensure that you will not sent an improper mode register.
                gen_manager = FullSpeedGenManager(self, dac_ch)
                sweep_settings = sweep_variables[sweep_variable]
                start_length = self.us2cycles(sweep_settings[0])
                end_length = self.us2cycles(sweep_settings[1])
                start_code = gen_manager.get_mode_code(
                    length=start_length, outsel="dds"
                )
                end_code = gen_manager.get_mode_code(length=end_length, outsel="dds")

                # The register containing the pulse length as the last 16 bits is referred to as the "mode" register.
                sweep_register = self.get_gen_reg(dac_ch, "mode")
                self.add_sweep(
                    QickSweep(
                        self, sweep_register, start_code, end_code, sweep_settings[2]
                    )
                )

        self.synci(200)  # Give processor some time to configure pulses

    def body(self):
        p: S21Protocol = self.cfg["protocol"]

        self.measure(
            adcs=[p.adc.channel],
            pulse_ch=p.dac.channel,
            adc_trig_offset=p.adc_trig_offset.get_raw(),
            t="auto",
            wait=True,
            syncdelay=p.relax_delay.get_raw(),
        )
