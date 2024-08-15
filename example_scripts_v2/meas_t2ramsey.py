from header import *

name = Path(__file__).name[:-3]

p = RamseyProtocol(qick_instrument, ge_half_pi_pulse, readout)
p.hard_avgs.set(1000)
p.final_delay.set(500e-6)
p.delay.time.set(QickSweep1D("delay", 1e-6, 50e-6))
p.half_pi_pulse_2.phase.set(QickSweep1D("phase", 0, 270))

p.run(
    Measurement(experiment, station, name),
    hardware_loop_counts={"delay": 50, "phase": 4},
)
