from header import *

ge_half_pi_pulse_2 = ge_half_pi_pulse.copy("ge_half_pi_pulse_2")
ge_half_pi_pulse_2.phase.set(QickSweep1D("phase", 0, 270))

qi.set_macro_list(
    [
        PlayPulse(qi, ge_half_pi_pulse),
        DelayAuto(qi, QickSweep1D("delay", 0.1e-6, 5e-6)),
        PlayPulse(qi, ge_half_pi_pulse_2),
        *readout,
    ]
)

qi.hard_avgs.set(1000)
qi.final_delay.set(200e-6)

qi.run(
    Measurement(station=station, name=Path(__file__).name[:-3]),
    hardware_loop_counts={"delay": 50, "phase": 4},
)
