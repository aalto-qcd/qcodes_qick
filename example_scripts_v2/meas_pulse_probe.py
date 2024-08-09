from header import *

name = os.path.basename(__file__)[:-3]

qubit_pulse = ConstantPulse(qick_instrument, qubit_dac, "qubit_pulse")
qubit_pulse.gain.set(0.9)
qubit_pulse.length.set(100e-6)

p = PulseProbeProtocol(qick_instrument, qubit_pulse, readout)
p.hard_avgs.set(100)
p.soft_avgs.set(1)
p.final_delay.set(3e-3)

p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep(qubit_pulse.freq, 2.85e9, 2.95e9, 101),
    ],
)
