from header import *

name = os.path.basename(__file__)[:-3]

readout_pulse.gain.set(0.9)
readout_pulse.freq.set(6e9)
readout_pulse.length.set(1e-6)
readout_pulse.wait_before.set(0)
readout_pulse.wait_after.set(10e-6)
readout_pulse.adc_length.set(readout_pulse.length.get())
p = S21Protocol(qick_instrument, readout_pulse)
p.hard_avgs.set(1000)
p.soft_avgs.set(1)
p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep(readout_pulse.adc_trig_offset, 0, 2e-6, 201),
    ],
)
