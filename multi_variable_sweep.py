import qcodes as qc
from qcodes.instrument import Instrument
from qick import *
from qick.averager_program import QickSweep
from qick.qick_asm import FullSpeedGenManager
import numpy as np


class MultiVariableSweepProgram(NDAveragerProgram):
    """
    This class performs a hardware loop sweep over one or more registers 
    in the board. The limit is seven registers.
    Refer to: https://qick-docs.readthedocs.io/en/latest/_modules/qick/averager_program.html#NDAveragerProgram


    Methods
    -------
    initialize(self):
        Initializes the program and defines important variables and registers.
        The sweeps are defined by self.add_sweep calls.
    body(self):
        Defines the structure of the actual measurement and will be looped over reps times.
    """
    def initialize(self):
    
        cfg = self.cfg

        #Defining local variables.
        qubit_ch = cfg["qubit_ch"]
        freq = self.freq2reg(cfg["pulse_freq"], gen_ch=qubit_ch, res_ch=cfg["res_ch"][0])
        phase = self.deg2reg(cfg["pulse_phase"], gen_ch=qubit_ch)
        gain = cfg["pulse_gain"]
        sweep_variables = cfg["sweep_variables"]

        #Declare signal generators and readout
        self.declare_gen(ch=cfg["qubit_ch"], nqz=1, res_ch=cfg["res_ch"])
        self.declare_readout(ch=ch, length=self.cfg["readout_length"],
                             freq=self.cfg["pulse_freq"], gen_ch=cfg["qubit_ch"])

        self.set_pulse_registers(ch=qubit_ch, style="const", freq=freq, phase=phase, gain=gain, length=cfg["length"])

        for sweep_variable in sweep_variables:
            if sweep_variable == "length":
                
                #Getting the gen manager for calculating the correct start and end points of the mode register.
                #Thus, by utilizing these methods you may ensure that you will not sent an improper mode register.
                gen_manager = FullSpeedGenManager(self, cfg["qubit_ch"]) 
                sweep_settings = sweep_variables[sweep_variable]
                start_code = gen_manager.get_mode_code(length=sweep_settings[0], outsel="dds")
                end_code = gen_manager.get_mode_code(length=sweep_settings[1], outsel="dds")

                print(self.cycles2us(sweep_settings[0]))
                print(self.cycles2us(sweep_settings[1]))
                #The register containing the pulse length as the last 16 bits is referred to as the "mode" register.
                sweep_register = self.get_gen_reg(cfg["qubit_ch"], "mode")
                self.add_sweep(QickSweep(self, sweep_register, start_code, end_code, sweep_settings[2]))
            else:
                sweep_settings = sweep_variables[sweep_variable]
                sweep_register = self.get_gen_reg(cfg["qubit_ch"], sweep_variable)
                self.add_sweep(QickSweep(self, sweep_register, sweep_settings[0], sweep_settings[1], sweep_settings[2]))


        self.synci(200)  #Give processor some time to configure pulses

    def body(self):

        self.measure(pulse_ch=self.cfg["qubit_ch"],
                     adcs=self.res_ch,
                     pins=[0],
                     adc_trig_offset=self.cfg["adc_trig_offset"],
                     wait=True,
                     syncdelay=self.us2cycles(self.cfg["relax_delay"]))
























