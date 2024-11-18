from header import *

ge_minus_pi_pulse = ge_pi_pulse.copy("ge_minus_pi_pulse")
ge_minus_pi_pulse.gain.set(-ge_pi_pulse.gain.get())

qi.set_macro_list(
    [
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        PlayPulse(qi, ge_pi_pulse),
        PlayPulse(qi, ge_minus_pi_pulse),
        *readout(),
    ]
)

qi.hard_avgs.set(1000)
qi.final_delay.set(200e-6)

qi.run(
    Measurement(station=station, name=Path(__file__).name[:-3]),
    software_sweeps=[
        SoftwareSweep(ge_envelope.alpha, -0.2, 0, 101),
    ],
)
