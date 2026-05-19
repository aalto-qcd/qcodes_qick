from header import *

name = os.path.basename(__file__)[:-3]

qubit_pulse = ConstantPulse(qick_instrument, qubit_dac)
qubit_pulse.length(100e-6)
readout_pulse.gain.set(0.1)
readout.wait_after.set(10e-6)
p = PulseProbeProtocol(qick_instrument, qubit_pulse, readout)
p.hard_avgs(1000)
p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep(qubit_pulse.gain, [0.0009, 0.009, 0.09, 0.9]),
    ],
    hardware_sweeps=[
        HardwareSweep(qubit_pulse.freq, 2.7e9, 3.0e9, 601),
    ],
)
