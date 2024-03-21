import os

from qcodes import (
    Measurement,
    Station,
    initialise_or_create_database_at,
    load_or_create_experiment,
)

from qcodes_qick import HardwareSweep, QickInstrument, SoftwareSweep
from qcodes_qick.instructions import *
from qcodes_qick.protocols import *

experiment_name = "loopback"
sample_name = "none"
wiring = [
    "ZCU216-DAC0_230 - balun_5-6GHz - balun_5-6GHz - ZCU216-ADC0_226",
]

initialise_or_create_database_at(f"./database/{experiment_name}.db")
experiment = load_or_create_experiment(experiment_name, sample_name)

station = Station()
station.metadata["wiring"] = wiring
qick_instrument = QickInstrument("QickInstrument", "10.0.100.16")
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
