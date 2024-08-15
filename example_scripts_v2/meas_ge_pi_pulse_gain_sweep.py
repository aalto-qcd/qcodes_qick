from header import *

name = Path(__file__).name[:-3]

p = PulseProbeProtocol(qick_instrument, ge_pi_pulse, readout)
ge_pi_pulse.gain(QickSweep1D("gain", 0, 1))
p.qubit_pulse_count.set(10)
p.hard_avgs.set(1000)
p.final_delay.set(500e-6)

p.run(
    Measurement(experiment, station, name),
    hardware_loop_counts={"gain": 101},
)
