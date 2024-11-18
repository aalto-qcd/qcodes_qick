from header import *

ge_pulse = ConstantPulse(qubit_dac, "ge_pulse")
ge_pulse.gain.set(0.01)
ge_pulse.freq.set(QickSweep1D("freq", 3.43e9, 3.45e9))
ge_pulse.length.set(QickSweep1D("length", 0.1e-6, 4e-6))

qi.set_macro_list(
    [
        PlayPulse(qi, ge_pulse),
        *readout(),
    ]
)

qi.hard_avgs.set(1000)
qi.final_delay.set(200e-6)

qi.run(
    Measurement(station=station, name=Path(__file__).name[:-3]),
    hardware_loop_counts={"length": 40, "freq": 41},
)
