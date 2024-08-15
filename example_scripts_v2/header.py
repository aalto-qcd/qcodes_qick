import sys
from pathlib import Path

from qcodes import (
    Measurement,
    Station,
    initialise_or_create_database_at,
    load_or_create_experiment,
)
from qick.asm_v2 import QickSweep1D
from valon_5015 import valon_5015

from qcodes_qick import QickInstrument
from qcodes_qick.envelopes_v2 import *
from qcodes_qick.instructions_v2 import *
from qcodes_qick.muxed_dac import MuxedDacChannel
from qcodes_qick.protocol_base_v2 import SoftwareSweep
from qcodes_qick.protocols_v2 import *

experiment_name = "BF4-CD7"
sample_name = "QCage.24+EITR3_2-2_qubit2"
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
valon3 - 1500mm - 9in - splitter_S
splitter_1 - L - VBF-7900+ - 9in - mixer1_LO
splitter_2 - L - VBF-7900+ - 9in - mixer2_LO
pynq2_DAC2_230 - balun1-4GHz - 12in - VBFZ-2000-S+ - L - mixer1_IF
mixer1_RF - VBFZ-5500-S+ - 1500mm - sideloader5-3
sideloader2-2 - 1500mm - VBFZ-5500-S+ - mixer2_RF
mixer2_IF - L - VBFZ-2000-S+ - 24in - balun1-4GHz - pynq2_ADC0_226

Qubit control:
pynq2_DAC0_230 - balun1-4GHz - 12in - VLFG-3800+ - 1500mm - 20dB - sideloader5-5
"""

initialise_or_create_database_at(Path(__file__).parent / "database.db")
experiment = load_or_create_experiment(experiment_name, sample_name)

station = Station()
station.metadata["wiring"] = wiring
qick_instrument: QickInstrument = QickInstrument("10.0.100.17")
station.add_component(qick_instrument)

valon3 = valon_5015("valon3", "10.0.100.23")
valon3.CW_frequency.set(8e9)
valon3.CW_power.set(15)
station.add_component(valon3)

qubit_dac = qick_instrument.dacs[0]
readout_dac = qick_instrument.dacs[1]
assert isinstance(readout_dac, MuxedDacChannel)
readout_adc = qick_instrument.adcs[0]
readout_dac.matching_adc.set(readout_adc.channel_num)
readout_adc.matching_dac.set(readout_dac.channel_num)
readout_dac.nqz.set(1)
readout_dac.tones[0].freq.set(2.176e9)
readout_dac.tones[0].gain.set(0.1)
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

gaussian = GaussianEnvelope(qick_instrument, qubit_dac, "gaussian")
gaussian.sigma.set(20e-9)
gaussian.length.set(100e-9)

ge_pi_pulse = Pulse(qick_instrument, gaussian, "ge_pi_pulse")
ge_pi_pulse.gain.set(0.59)
ge_pi_pulse.freq.set(3.864e9)

ge_half_pi_pulse = ge_pi_pulse.copy("ge_half_pi_pulse")
ge_half_pi_pulse.gain.set(ge_pi_pulse.gain.get() / 2)

ef_pi_pulse = Pulse(qick_instrument, gaussian, "ef_pi_pulse")
ef_pi_pulse.gain.set(0.35)
ef_pi_pulse.freq.set(3.717e9)

ef_half_pi_pulse = ef_pi_pulse.copy("ef_half_pi_pulse")
ef_half_pi_pulse.gain.set(ef_pi_pulse.gain.get() / 2)
