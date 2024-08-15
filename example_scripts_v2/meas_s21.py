from header import *

name = Path(__file__).name[:-3]

p = S21Protocol(qick_instrument, readout)
p.hard_avgs.set(1000)

p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep([readout_dac.tones[0].freq, readout_adc.freq], 1e9, 3e9, 1001),
    ]
)
