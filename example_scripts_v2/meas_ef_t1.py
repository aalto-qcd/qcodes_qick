from header import *

name = Path(__file__).name[:-3]

p = EfT1Protocol(qick_instrument, ge_pi_pulse, ge_half_pi_pulse, ef_pi_pulse, readout)
p.hard_avgs.set(1000)
p.final_delay.set(500e-6)
p.delay.time.set(QickSweep1D("delay", 0.1e-6, 50e-6))

p.run(
    Measurement(experiment, station, name),
    hardware_loop_counts={"delay": 101},
)
