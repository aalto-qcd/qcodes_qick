from header import *

name = os.path.basename(__file__)[:-3]

p = PulseProbeProtocol(qick_instrument, pi_pulse, readout)
p.qubit_pulse_count(10)
p.hard_avgs(1000)
p.soft_avgs(1)
p.run(
    Measurement(experiment, station, name),
    hardware_sweeps=[
        HardwareSweep(pi_pulse.gain, 0, 1, 101),
    ],
)
