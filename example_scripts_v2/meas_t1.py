from header import *

name = Path(__file__).name[:-3]

p = PulseProbeProtocol(qick_instrument, ge_pi_pulse, readout)
p.hard_avgs.set(1000)
p.final_delay.set(500e-6)
readout.wait_before(QickSweep1D("delay", 10e-6, 500e-6))

p.run(
    Measurement(experiment, station, name),
    hardware_loop_counts={"delay": 100},
)
