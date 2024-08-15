from header import *

name = Path(__file__).name[:-3]

ge_pulse = ConstantPulse(qick_instrument, qubit_dac)
ge_pulse.gain.set(0.01)
ge_pulse.freq.set(QickSweep1D("freq", 3.86e9, 3.88e9))
ge_pulse.length.set(QickSweep1D("length", 1e-6, 11e-6))

p = PulseProbeProtocol(qick_instrument, ge_pulse, readout)
p.hard_avgs.set(1000)
p.final_delay.set(500e-6)

p.run(
    Measurement(experiment, station, name),
    hardware_loop_counts={"length": 51, "freq": 51},
)
