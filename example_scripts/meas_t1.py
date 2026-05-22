from header import *

name = os.path.basename(__file__)[:-3]

p = PulseProbeProtocol(qick_instrument, pi_pulse, readout)
p.hard_avgs(100)
p.run(
    Measurement(experiment, station, name),
    hardware_sweeps=[
        HardwareSweep(readout.wait_before, 0, 2e-3, 101, skip_first=True),
        HardwareSweep(pi_pulse.gain, 0, pi_pulse.gain.get(), 2),
    ],
)
