from header import *

name = os.path.basename(__file__)[:-3]

readout_pulse.gain.set(0.1)
p = PulseProbeProtocol(qick_instrument, pi_pulse, readout)
p.hard_avgs.set(100)
p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep([readout_pulse.freq, readout_adc.freq], 6.317e9, 6.323e9, 601),
    ],
    hardware_sweeps=[
        HardwareSweep(pi_pulse.gain, 0, pi_pulse.gain.get(), 2),
    ],
)
