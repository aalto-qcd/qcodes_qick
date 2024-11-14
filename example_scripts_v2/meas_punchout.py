from header import *

readout_pulse.length.set(100e-6)
readout_adc.length.set(readout_pulse.length.get())

qi.set_macro_list(
    [
        *readout(),
    ]
)

qi.hard_avgs.set(1000)

qi.run(
    Measurement(station=station, name=Path(__file__).name[:-3]),
    software_sweeps=[
        SoftwareSweep(readout_pulse.gain, 0, 1, 21, skip_first=True),
        SoftwareSweep([readout_pulse.freq, readout_adc.freq], 5.5e9, 6.5e9, 51),
    ],
)
