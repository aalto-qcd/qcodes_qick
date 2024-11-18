from header import *

ge_pi_pulse.gain.set(QickSweep1D("gain", 0, 0.15))

qi.set_macro_list(
    [
        PlayPulse(qi, ge_pi_pulse),
        *readout(),
    ]
)

qi.hard_avgs.set(10000)
qi.final_delay.set(200e-6)

qi.run(
    Measurement(station=station, name=Path(__file__).name[:-3]),
    hardware_loop_counts={"gain": 2},
    acquisition_mode="accumulated shots",
)
