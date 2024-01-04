import qcodes as qc
from qcodes.instrument import Instrument
from qick import *
from qick.averager_program import QickSweep
import numpy as np


class HardwareSweepProgram(NDAveragerProgram):
    """
    This class performs a hardware loop sweep over one or more registers 
    in the board. The limit is seven registers.


    Methods
    -------
    initialize(self):
        Initializes the program and defines important variables and registers.
        The sweeps are defined by self.add_sweep calls.
    body(self):
        Defines the structure of the actual measurement and will be looped over reps times.
    """
    def initialize(self):
        """
        Initialization of the qick program, and configuration of the ND-sweeps is performed in this method.
        """

        cfg = self.cfg

        #Defining local variables.
        qubit_ch = cfg["qubit_ch"]
        freq = self.freq2reg(cfg["pulse_freq"], gen_ch=qubit_ch, ro_ch=cfg["res_ch"])
        phase = self.deg2reg(cfg["pulse_phase"], gen_ch=qubit_ch)
        gain = cfg["pulse_gain"]
        length = self.us2cycles(cfg['pulse_length'], gen_ch=self.cfg['qubit_ch'])
        sweep_variables = cfg["sweep_variables"]

        #Declare signal generators and readout
        self.declare_gen(ch=cfg["qubit_ch"], nqz=cfg["nqz"], ro_ch=cfg["res_ch"])
        self.declare_readout(ch=cfg["res_ch"], length=self.us2cycles(self.cfg['readout_length'], ro_ch = self.cfg['res_ch']),
                             freq=self.cfg["pulse_freq"], gen_ch=cfg["qubit_ch"])

        self.set_pulse_registers(ch=qubit_ch, style="const", freq=freq, phase=phase, gain=gain, length=length)

        for sweep_variable in sweep_variables:
            if sweep_variable == "pulse_length":
                
                #Getting the gen manager for calculating the correct start and end points of the mode register.
                #Thus, by utilizing these methods you may ensure that you will not sent an improper mode register.
                gen_manager = FullSpeedGenManager(self, cfg["qubit_ch"]) 
                sweep_settings = sweep_variables[sweep_variable]
                start_length = self.us2cycles(sweep_settings[0])
                end_length = self.us2cycles(sweep_settings[1])
                start_code = gen_manager.get_mode_code(length=start_length, outsel="dds")
                end_code = gen_manager.get_mode_code(length=end_length, outsel="dds")

                #The register containing the pulse length as the last 16 bits is referred to as the "mode" register.
                sweep_register = self.get_gen_reg(cfg["qubit_ch"], "mode")
                self.add_sweep(QickSweep(self, sweep_register, start_code, end_code, sweep_settings[2]))
            else:
                sweep_settings = sweep_variables[sweep_variable]
                sweep_register = self.get_gen_reg(cfg["qubit_ch"], sweep_variable.replace('pulse_', ''))
                self.add_sweep(QickSweep(self, sweep_register, sweep_settings[0], sweep_settings[1], sweep_settings[2]))


        self.synci(200)  #Give processor some time to configure pulses

    def body(self):
        """
            The main structure of the measurement is just the measurement,
            but the add_sweep commands in the initialize method add inner loops
            into the qick program instructions.
        """

        self.measure(pulse_ch=self.cfg["qubit_ch"],
                     adcs=[self.cfg["res_ch"]],
                     pins=[0],
                     adc_trig_offset=self.cfg["adc_trig_offset"],
                     wait=True,
                     syncdelay=self.us2cycles(self.cfg["relax_delay"]))


class LoopbackProgram(AveragerProgram):
    """
    Forgotten class for testing.
    """
    def initialize(self):

        cfg = self.cfg

        #Defining local variables.
        qubit_ch = cfg["qubit_ch"]
        freq = self.freq2reg(cfg["pulse_freq"], gen_ch=qubit_ch, ro_ch=cfg["res_ch"])
        phase = self.deg2reg(cfg["pulse_phase"], gen_ch=qubit_ch)
        gain = cfg["pulse_gain"]

        #Declare signal generators and readout
        self.declare_gen(ch=cfg["qubit_ch"], nqz=cfg["nqz"], ro_ch=cfg["res_ch"])
        self.declare_readout(ch=cfg["res_ch"], length=self.cfg["readout_length"],
                             freq=self.cfg["pulse_freq"], gen_ch=cfg["qubit_ch"])

        self.set_pulse_registers(ch=qubit_ch, style="const", freq=freq, phase=phase, gain=gain, length=cfg["pulse_length"])

        self.synci(200)  # give processor some time to configure pulses


    def body(self):
        self.measure(pulse_ch        = self.cfg['res_ch'],
                     adcs            = self.ro_chs,
                     pins            = [0],
                     adc_trig_offset = self.cfg['adc_trig_offset'],
                     )























