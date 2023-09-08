import qcodes as qc
from qcodes.instrument import Instrument
from qick import *
from qick.averager_program import QickSweep
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
        res_ch = cfg["res_ch"]
        freq = self.freq2reg(cfg["pulse_freq"], gen_ch=res_ch, ro_ch=cfg["ro_chs"][0])
        phase = self.deg2reg(cfg["pulse_phase"], gen_ch=res_ch)
        gain = cfg["pulse_gain"]
        sweep_variables = cfg["sweep_variables"]

        #Declare signal generators and readout
        self.declare_gen(ch=cfg["res_ch"], nqz=1, ro_ch=cfg["ro_chs"][0])
        for ch in cfg["ro_chs"]:
            self.declare_readout(ch=ch, length=self.cfg["readout_length"],
                                 freq=self.cfg["pulse_freq"], gen_ch=cfg["res_ch"])
        self.set_pulse_registers(ch=res_ch, style="const", freq=freq, phase=phase, gain=gain, length=cfg["length"])

        for sweep_variable in sweep_variables:
            if sweep_variable == "length":
                pass

                sweep_settings = sweep_variables[sweep_variable]
                #The register containing the pulse length as the last 16 bits is referred to as the "mode" register.
                sweep_register = self.get_gen_reg(cfg["res_ch"], "mode")
                print(sweep_register.init_val)
                self.add_sweep(QickSweep(self, sweep_register, sweep_settings[0], sweep_settings[1], sweep_settings[2]))
            else:
                sweep_settings = sweep_variables[sweep_variable]
                sweep_register = self.get_gen_reg(cfg["res_ch"], sweep_variable)
                self.add_sweep(QickSweep(self, sweep_register, sweep_settings[0], sweep_settings[1], sweep_settings[2]))


        self.synci(200)  #Give processor some time to configure pulses

    def body(self):

        self.measure(pulse_ch=self.cfg["res_ch"],
                     adcs=self.ro_chs,
                     pins=[0],
                     adc_trig_offset=self.cfg["adc_trig_offset"],
                     wait=True,
                     syncdelay=self.us2cycles(self.cfg["relax_delay"]))



















































































































