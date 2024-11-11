from header import *

qi.set_macro_list(
    [
        PlayPulse(qi, ge_half_pi_pulse),
        DelayAuto(qi, QickSweep1D("delay", 0.05e-6, 5e-6)),
        PlayPulse(qi, ge_pi_pulse),
        DelayAuto(qi, QickSweep1D("delay", 0.05e-6, 5e-6)),
        PlayPulse(qi, ge_half_pi_pulse),
        *readout,
    ]
)

qi.hard_avgs.set(1000)
qi.final_delay.set(200e-6)

qi.run(
    Measurement(station=station, name=Path(__file__).name[:-3]),
    hardware_loop_counts={"delay": 100},
)
