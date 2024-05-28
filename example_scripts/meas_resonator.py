from .header import *

name = os.path.basename(__file__)[:-3]

readout_pulse.gain.set(0.02)
readout_pulse.length.set(10e-6)
readout_adc.length.set(readout_pulse.length.set())
readout.wait_before.set(0)
readout.wait_after.set(10e-6)
p = S21Protocol(qick_instrument, readout)
p.hard_avgs.set(1000)
p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep([readout_pulse.freq, readout_adc.freq], 6.317e9, 6.323e9, 601),
    ],
)
