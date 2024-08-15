from header import *

name = Path(__file__).name[:-3]

p = S21Protocol(qick_instrument, readout)
p.hard_avgs.set(1000)

p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep(readout_dac.tones[0].gain, 0, 1, 21, skip_first=True),
        SoftwareSweep(
            [readout_dac.tones[0].freq, readout_adc.freq], 2.15e9, 2.2e9, 101
        ),
    ],
)
