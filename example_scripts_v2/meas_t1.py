from header import *

qi.set_macro_list(
    [
        PlayPulse(qi, ge_pi_pulse),
        DelayAuto(qi, t=QickSweep1D("delay", 2e-6, 200e-6)),
        *readout(),
    ]
)

qi.hard_avgs.set(1000)
qi.final_delay.set(200e-6)

qi.run(
    Measurement(station=station, name=Path(__file__).name[:-3]),
    hardware_loop_counts={"delay": 100},
)
