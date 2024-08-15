from header import *

name = Path(__file__).name[:-3]

readout_dac.tones[0].gain.set(0.1)

p = S21Protocol(qick_instrument, readout)
p.hard_avgs.set(1000)

p.run(
    Measurement(experiment, station, name),
    software_sweeps=[
        SoftwareSweep(
            [readout_dac.tones[0].freq, readout_adc.freq], 2.0e9, 2.05e9, 501
        ),
    ],
)
