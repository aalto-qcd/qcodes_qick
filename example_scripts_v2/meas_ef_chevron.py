from header import *

name = Path(__file__).name[:-3]

ef_pulse = ConstantPulse(qick_instrument, qubit_dac)
ef_pulse.gain.set(1)
ef_pulse.freq.set(QickSweep1D("freq", 3.6e9, 3.8e9))
ef_pulse.length.set(QickSweep1D("length", 0.1e-6, 2e-6))

p = EfPulseProbeProtocol(qick_instrument, ge_pi_pulse, ef_pulse, readout)
p.hard_avgs.set(1000)
p.final_delay.set(500e-6)

p.run(
    Measurement(experiment, station, name),
    hardware_loop_counts={"length": 21, "freq": 51},
)
