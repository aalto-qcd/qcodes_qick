import os

from qcodes import (
    Measurement,
    Station,
    initialise_or_create_database_at,
    load_or_create_experiment,
)

from qcodes_qick.instructions import *
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.protocol_base import HardwareSweep, SoftwareSweep
from qcodes_qick.protocols import *

experiment_name = "BF4-CD2"
sample_name = "cavity16_3D1_10-19"
wiring = [
    "dc = directional coupler ZUDC20-02183-S+",
    "FS725_10MHz - ZCU216-INPUT_REF_CLK",
    "ZCU216-DAC0_231 - balun_1-4GHz - 10in - ZX60-123LN-S+ - VLF-3400+ - dc-out",
    "ZCU216-DAC0_230 - balun_5-6GHz - 6in - 10dB - VHF-3100+ - dc-cpl",
    "dc-in - 50in - sideloader2-25",
    "sideloader2-2 - VHF4400+ - 50in - balun_5-6GHz - ZCU216-ADC0_226",
]

initialise_or_create_database_at(f"./database/{experiment_name}.db")
experiment = load_or_create_experiment(experiment_name, sample_name)

station = Station()
station.metadata["wiring"] = wiring
qick_instrument = QickInstrument("QickInstrument")
station.add_component(qick_instrument)

readout_dac = qick_instrument.dacs[0]
readout_dac.nqz.set(2)
readout_adc = qick_instrument.adcs[0]

readout_pulse = ReadoutPulse(qick_instrument, readout_dac, readout_adc)
readout_pulse.gain.set(0.4)
readout_pulse.freq.set(6.3203e9)
readout_pulse.length.set(10e-6)
readout_pulse.wait_before.set(100e-9)
readout_pulse.wait_after.set(2e-3)
readout_pulse.adc_trig_offset.set(0.5e-6)
readout_pulse.adc_length.set(readout_pulse.length.get())

qubit_dac = qick_instrument.dacs[4]
qubit_dac.nqz.set(1)

pi_pulse = GaussianPulse(qick_instrument, qubit_dac, "pi_pulse")
pi_pulse.gain.set(0.72)
pi_pulse.freq.set(2.9754e9)
pi_pulse.sigma.set(100e-9)
pi_pulse.length.set(400e-9)

half_pi_pulse = GaussianPulse(qick_instrument, qubit_dac, "half_pi_pulse")
half_pi_pulse.gain.set(pi_pulse.gain.get() / 2)
half_pi_pulse.freq.set(pi_pulse.freq.get())
half_pi_pulse.sigma.set(pi_pulse.sigma.get())
half_pi_pulse.length.set(pi_pulse.length.get())
