import os

from qcodes import (
    Measurement,
    Station,
    initialise_or_create_database_at,
    load_or_create_experiment,
)
from valon_5015 import valon_5015

from qcodes_qick import QickInstrument
from qcodes_qick.instructions_v2 import *
from qcodes_qick.muxed_dac import MuxedDacChannel
from qcodes_qick.protocol_base_v2 import SoftwareSweep
from qcodes_qick.protocols_v2 import *

experiment_name = "BF4-CD4"
sample_name = "QCage.24+EITR2_1-2_qubit2"
wiring = """
pynq2 = Xilinx ZCU216 + CLK104 + XM655
valon1 = Valon 5015
clock = SRS FS725
splitter = Mini-Circuits ZFSC-2-10G+
mixer1 = Mini-Circuits ZX05-153LH-S+
mixer2 = Mini-Circuits ZX05-153LH-S+
1500mm = Totoku TCF358AA1500
9in, 12in, 24in = Mini-Circuits FL086-9SM+, FL086-12SM+, FL086-24SM+

clock_10MHz - pynq2_INPUT_REF_CLK

Readout:
valon1 - 1500mm - 9in - splitter_S
splitter_1 - L - VHF-7150+ - 9in - mixer1_LO
splitter_2 - L - VHF-7150+ - 9in - mixer2_LO
pynq2_DAC2_230 - balun1-4GHz - 12in - VBFZ-2000-S+ - L - mixer1_IF
mixer1_RF - VBFZ-5500-S+ - 1500mm - sideloader2-12
sideloader2-2 - 1500mm - VBFZ-5500-S+ - mixer2_RF
mixer2_IF - L - VBFZ-2000-S+ - 24in - balun1-4GHz - pynq2_ADC0_226

Qubit control:
pynq2_DAC0_230 - balun1-4GHz - 12in - VLF-3400+ - 1500mm - sideloader2-13
"""

initialise_or_create_database_at(f"./database/{experiment_name}.db")
experiment = load_or_create_experiment(experiment_name, sample_name)

station = Station()
station.metadata["wiring"] = wiring
qick_instrument: QickInstrument = QickInstrument("10.0.100.17")
station.add_component(qick_instrument)

valon1 = valon_5015("valon1", "10.0.100.21")
valon1.CW_frequency.set(8e9)
valon1.CW_power.set(15)
station.add_component(valon1)

qubit_dac = qick_instrument.dacs[0]
readout_dac = qick_instrument.dacs[1]
assert isinstance(readout_dac, MuxedDacChannel)
readout_adc = qick_instrument.adcs[0]
readout_dac.matching_adc.set(readout_adc.channel_num)
readout_adc.matching_dac.set(readout_dac.channel_num)
readout_dac.nqz.set(1)
readout_dac.tones[0].freq.set(2.022e9)
readout_dac.tones[0].gain.set(0.2)
readout_adc.freq.set(readout_dac.tones[0].freq.get())

readout_pulse = MuxedConstantPulse(qick_instrument, readout_dac, "readout_pulse")
readout_pulse.length.set(10e-6)
readout_pulse.tone_nums.set([0])
readout_adc.length.set(readout_pulse.length.get())

readout = Readout(qick_instrument, readout_pulse, readout_adc)
readout.wait_before.set(100e-9)
readout.wait_after.set(100e-9)
readout.adc_trig_offset.set(0.45e-6)
readout.wait_for_adc.set(True)

qubit_dac = qick_instrument.dacs[0]
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
