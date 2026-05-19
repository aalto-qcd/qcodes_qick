from header import *

name = os.path.basename(__file__)[:-3]

readout_pulse.gain.set(0.9)
readout_pulse.freq.set(6e9)
readout_pulse.length.set(1e-6)
readout_adc.freq.set(readout_pulse.freq.get())
readout_adc.length.set(readout_pulse.length.get())
readout.wait_before.set(0)
readout.wait_after.set(10e-6)
p = S21Protocol(qick_instrument, readout)
p.hard_avgs.set(1000)
p.soft_avgs.set(1)
p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep(readout.adc_trig_offset, 0, 2e-6, 201),
    ],
)
