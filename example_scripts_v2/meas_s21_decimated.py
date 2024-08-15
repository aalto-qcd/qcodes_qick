from header import *

name = Path(__file__).name[:-3]

readout_dac.tones[0].gain.set(1)
readout_pulse.length.set(1e-6)
readout_adc.length.set(3e-6)
readout.adc_trig_offset(0)

p = S21Protocol(qick_instrument, readout)
p.hard_avgs.set(1)
p.soft_avgs.set(1000)

p.run(
    Measurement(experiment, station, name),
    decimated=True
)
