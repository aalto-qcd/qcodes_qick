# qcodes_qick

A [QCoDeS](https://github.com/microsoft/qcodes) driver for [QICK](https://github.com/openquantumhardware/qick). Usable but still under active development. Pull requests are welcomed!

## Development goals

- This should be a thin wrapper that directly exposes all features of QICK.
- Pulses ("[`instructions`](https://github.com/aalto-qcd/qcodes_qick/tree/main/qcodes_qick/instructions)") and pulse sequences ("[`protocols`](https://github.com/aalto-qcd/qcodes_qick/tree/main/qcodes_qick/protocols)") should be parameterized such that they can be fully reproduced based on the [QCoDeS snapshot](https://microsoft.github.io/Qcodes/examples/DataSet/Working%20with%20snapshots.html) that gets saved with every dataset.

## Getting started

1. Clone or copy this repository to a local PC.
2. `pip install -e path\to\repository`
3. Start the Pyro4 nameserver (see [here](https://github.com/openquantumhardware/qick/blob/main/pyro4/00_nameserver.ipynb), use port 8888) and the QICK server (see [here](https://github.com/openquantumhardware/qick/blob/main/pyro4/01_server.ipynb)) on a Xilinx board.
4. Check the connection and the channel number assignment:
    ```python
    from qcodes_qick import QickInstrument
    qick_instrument = QickInstrument("ip.address.of.board")
    print(qick_instrument.soccfg)
    ```
5. Copy the scripts in the folder [`example_scripts`](https://github.com/aalto-qcd/qcodes_qick/tree/main/example_scripts) into your folder.
6. Edit [`header.py`](https://github.com/aalto-qcd/qcodes_qick/blob/main/example_scripts/header.py):
    - Specify the IP address of the board by editing the line like
      ```python
      qick_instrument = QickInstrument("ip.address.of.board")
      ```
    - Specify DAC/ADC channel numbers by editing the lines like
      ```python
      readout_dac = qick_instrument.dacs[channel_number]
      ```
7. Run the example scripts:
    - [`meas_s21_vs_adc_trig_offset.py`](https://github.com/aalto-qcd/qcodes_qick/blob/main/example_scripts/meas_s21_vs_adc_trig_offset.py): Optimize the ADC trigger offset
    - [`meas_resonator.py`](https://github.com/aalto-qcd/qcodes_qick/blob/main/example_scripts/meas_resonator.py): Measure S21 vs frequency
    - [`meas_punchout.py`](https://github.com/aalto-qcd/qcodes_qick/blob/main/example_scripts/meas_punchout.py): Measure S21 vs frequency and amplitude
    - [`meas_pulse_probe_2d.py`](https://github.com/aalto-qcd/qcodes_qick/blob/main/example_scripts/meas_pulse_probe_2d.py): Pulse probe spectroscopy of a qubit dispersively coupled to a resonator
    - [`meas_pi_pulse_gain_sweep.py`](https://github.com/aalto-qcd/qcodes_qick/blob/main/example_scripts/meas_pi_pulse_gain_sweep.py): Optimize the amplitude of a pi pulse (play 10 pi pulses and readout)
    - [`meas_resonator_vs_qubit_state.py`](https://github.com/aalto-qcd/qcodes_qick/blob/main/example_scripts/meas_resonator_vs_qubit_state.py): Measure resonator spectra with the qubit in the ground and excited states
    - [`meas_t1.py`](https://github.com/aalto-qcd/qcodes_qick/blob/main/example_scripts/meas_t1.py): Measure the T1 of the qubit
