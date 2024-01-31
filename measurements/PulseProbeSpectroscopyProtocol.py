import qcodes as qc
import numpy as np
import itertools
from qick import *
from qcodes.instrument import Instrument, ManualParameter
from qcodes.utils.validators import Numbers, MultiType, Ints 
from measurements.Protocols import Protocol
from typing import List, Dict, Any 




class PulseProbeSpectroscopyProtocol(Protocol):
    """
        This protocol initializes and runs a pulse probe spectroscopy measurement 
        program, and correctly formats the output into a desired form. 
    """
    def __init__(self, name="PPS_Protocol"):
        """
        Initialize the protocol object.
            
        """
        super().__init__(name)

        self.required_DACs = {'qubit': 'Qubit probe channel', 'readout' : 'Readout pulse channel', }
        self.required_ADCs = {'adc' : 'Readout adc channel' }
        self.validated_IO = {'qubit' : None, 'readout': None, 'adc': None}

        self.sensible_defaults = {
                                   "adc_trig_offset"  : 100,    # -- Clock ticks
                                   "relax_delay"      : 1,      # -- us 
                                   "readout_lenght"   : 5,      # -- MHz
                                   "reps"             : 400 }   # -- us

        self.add_parameter('adc_trig_offset',
                            parameter_class=ManualParameter,
                            label='Delay between measuring pulse and ADC initialization',
                            vals = Ints(*[0,100000]),
                            unit = 'Clock ticks', 
                            initial_value = 100)

        self.add_parameter('relax_delay',
                            parameter_class=ManualParameter,
                            label='Delay between reps',
                            vals = Numbers(*[0,100000]),
                            unit = 'us', 
                            initial_value = 0.1)


        self.add_parameter('reps',
                            parameter_class=ManualParameter,
                            label='Measurement repetitions',
                            vals = Ints(0,5000),
                            initial_value = 400)

        self.add_parameter('readout_pulse_delay',
                            parameter_class=ManualParameter,
                            label='Delay between ending the probe pulse and initiating the readout pulse',
                            vals = Numbers(*[0,100]),
                            unit = 'us',
                            initial_value = 0.05)

    def compile_hardware_sweep_dict(self, sweep_configuration, internal_variables):
        """
        This can be hardcoded for now.
        """

        internal_config = {}
        internal_config["start"] = self.validated_IO['qubit'].pulse_freq.get()
        internal_config["expts"] = 1
        internal_config["step"] = 0 

        for parameter, values in sweep_configuration.items():
            if parameter == internal_variables['qubit_freq']:
                internal_config["start"] = values[0]
                internal_config["expts"] = values[-1]
                internal_config["step"] = (values[-1]-values[0])/len(values)
                self.add_sweep_parameter(isHardware = True, parameter = parameter)

        return internal_config

    def initialize_qick_program(self, soc, soccfg, sweep_configuration):
        """ 
        Initialize the qick soc and qick config
        
        """
        


        self.soc = soc
        self.soccfg = soccfg

        #This is the only part where you need to hard code the qick config dictionary, this
        #is due to the fact that the qick config dictionary expect certain hard coded entries.
         
        # (Protocol specific) config corresponding to parameters that can only be swept outside of 
        # the qick program hardware loop
        external_parameters = { 
                    #These are protocol specific, inherent parameter values
                    'reps' : self.reps,
                    'relax_delay' : self.relax_delay,
                    'adc_trig_offset' : self.adc_trig_offset,
                    'readout_pulse_delay' : self.readout_pulse_delay,

                    #For the PulseProbeSpectroscopy program, readout probe pulse
                    #lenght is a good readout lenght
                    'readout_length' : self.validated_IO['readout'].pulse_length,

                    #These are channel specific values 
                    'qubit_ch' : self.validated_IO['qubit'].channel,
                    'qubit_nqz' : self.validated_IO['qubit'].nqz,
                    'qubit_gain' : self.validated_IO['qubit'].pulse_gain,
                    'qubit_phase' : self.validated_IO['qubit'].pulse_phase,
                    'qubit_length' : self.validated_IO['qubit'].pulse_length,


                    'cavity_ch' : self.validated_IO['readout'].channel,
                    'cavity_nqz' : self.validated_IO['readout'].nqz,
                    'cavity_gain' : self.validated_IO['readout'].pulse_gain,
                    'cavity_freq' : self.validated_IO['readout'].pulse_freq,
                    'cavity_phase' : self.validated_IO['readout'].pulse_phase,
                    'cavity_length' : self.validated_IO['readout'].pulse_length,

                    'ro_ch' : self.validated_IO['adc'].channel
                   }

        external_config = self.compile_software_sweep_dict( sweep_configuration, external_parameters )

        # Internal parameters that can be swept in hardware
        internal_parameters = { 
                    'qubit_freq' : self.validated_IO['qubit'].pulse_freq,
                   }

        internal_config = self.compile_hardware_sweep_dict(sweep_configuration, internal_parameters)
        qick_config = {**external_config, **internal_config}

        return qick_config, self.sweep_parameter_list

                
    def run_program(self, cfg : Dict[str, float]):
        """
        This method runs the program and returns the measurement 
        result.

        Return:
            expt_pts:
            list of arrays containing the coordinate values of 
            each variable for each measurement point
            avg_q:
            ND-array of avg_q values containing each measurement q value.
            avg_i:
            ND-array of avg_i values containing each measurement i value.
        """
        self.cfg = cfg.copy()
        expt_pts, avg_i, avg_q = self.run_hybrid_loop_program(cfg, PulseProbeSpectroscopyProgram)
        return expt_pts, avg_i, avg_q 

class PulseProbeSpectroscopyProgram(RAveragerProgram):

    def initialize(self):
        cfg=self.cfg

        #Qubit refers to the probe pulse
        #Res refers to readout
        #Cavity refers to the low power resonant probe

        #Defining local variables for qubit probing and readout.
        #The channel for the qubit probing is the channel corresponding
        #to the default pulse variables (pulse_lenght, pulse_phase, etc.)
        qubit_ch = cfg["qubit_ch"]
        probe_freq = self.freq2reg(cfg["start"], gen_ch=qubit_ch, ro_ch=cfg["ro_ch"])
        probe_phase = self.deg2reg(cfg["qubit_phase"], gen_ch=qubit_ch)
        probe_gain = round(cfg["qubit_gain"])
        probe_length = self.us2cycles(cfg['qubit_length'], gen_ch=qubit_ch)
        cavity_pulse_length = self.us2cycles(cfg['readout_length'], gen_ch=cfg["cavity_ch"])
        self.declare_gen(ch=cfg["cavity_ch"], nqz=cfg["cavity_nqz"]) #Cavity resonant probe
        self.declare_gen(ch=qubit_ch, nqz=cfg["qubit_nqz"]) #Qubit probe

        self.declare_readout(ch=cfg["ro_ch"], length=self.us2cycles(cfg["readout_length"]),
                             freq=cfg["cavity_freq"], gen_ch=cfg["cavity_ch"])

        #Find register pages
        self.q_rp=self.ch_page(qubit_ch)
        self.r_freq=self.sreg(qubit_ch, "freq")

        # Get dac register value for cavity frequecy
        cavity_freq=self.freq2reg(cfg["cavity_freq"], gen_ch=cfg["cavity_ch"], ro_ch=cfg["ro_ch"])

        #Get start and step size frequencies
        self.f_start = self.freq2reg(cfg["start"], gen_ch=cfg["qubit_ch"])
        self.f_step = self.freq2reg(cfg["step"], gen_ch=cfg["qubit_ch"])


        # add qubit and readout pulses to respective channels
        self.set_pulse_registers(ch=qubit_ch, style="const", freq=self.f_start, phase=probe_phase, gain=probe_gain,
                                 length=probe_length)

        self.set_pulse_registers(ch=cfg["cavity_ch"], style="const", freq=cavity_freq, phase=cfg["cavity_phase"], gain=cfg["cavity_gain"],
                                 length=cavity_pulse_length)

        self.sync_all(self.us2cycles(200))

    def body(self):
        self.pulse(ch=self.cfg["qubit_ch"])  #play probe pulse
        self.sync_all(self.us2cycles(cfg["readout_pulse_delay"])) # align channels and wait 50ns

        #trigger measurement, play measurement pulse, wait for qubit to relax
        self.measure(pulse_ch=self.cfg["cavity_ch"],
             adcs=[0],
             adc_trig_offset=round(self.cfg["adc_trig_offset"]),
             wait=True,
             syncdelay=self.us2cycles(self.cfg["relax_delay"]))

    def update(self):
        self.mathi(self.q_rp, self.r_freq, self.r_freq, '+', self.f_step) # update frequency list index

