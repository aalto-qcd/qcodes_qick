from header import *

name = Path(__file__).name[:-3]

ef_pi_pulse.gain.set(QickSweep1D("gain", 0, 1))

p = EfPulseProbeProtocol(qick_instrument, ge_pi_pulse, ef_pi_pulse, readout)
p.ef_pulse_count(1)
p.hard_avgs.set(1000)
p.final_delay.set(500e-6)

p.run(
    Measurement(experiment, station, name),
    hardware_loop_counts={"gain": 101},
)
