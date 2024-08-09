from header import *

name = os.path.basename(__file__)[:-3]

p = S21Protocol(qick_instrument, readout)
p.hard_avgs.set(1000)
p.soft_avgs.set(1)

p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep(
            readout_dac.tones[0].gain, 0, 1, 11, skip_first=True, skip_last=True
        ),
        SoftwareSweep(
            [readout_dac.tones[0].freq, readout_adc.freq], 2.0e9, 2.05e9, 101
        ),
    ],
)
