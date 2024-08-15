from header import *

name = Path(__file__).name[:-3]

qubit_pulse = ConstantPulse(qick_instrument, qubit_dac, "qubit_pulse")
qubit_pulse.freq.set(QickSweep1D("freq", 3.5e9, 4e9))
qubit_pulse.gain.set(QickSweep1D("gain", 0, 0.1))
qubit_pulse.length.set(100e-6)

p = PulseProbeProtocol(qick_instrument, qubit_pulse, readout)
p.hard_avgs.set(1000)
p.final_delay.set(100e-6)

p.run(
    Measurement(experiment, station, name),
    hardware_loop_counts={"gain": 11, "freq": 201},
)
