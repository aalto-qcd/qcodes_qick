from header import *

ge_pulse = ConstantPulse(qubit_dac, "ge_pulse")
ge_pulse.gain.set(QickSweep1D("gain", 0, 0.2))
ge_pulse.freq.set(QickSweep1D("freq", 2.8e9, 3.8e9))
ge_pulse.length.set(100e-6)

qi.set_macro_list(
    [
        PlayPulse(qi, ge_pulse),
        *readout,
    ]
)
qi.final_delay.set(100e-6)
qi.hard_avgs.set(1000)

qi.run(
    Measurement(station=station, name=Path(__file__).name[:-3]),
    hardware_loop_counts={"gain": 21, "freq": 501},
)
