import qcodes as qc
import numpy as np
import itertools
from qick import *
from qcodes.instrument import Instrument, ManualParameter
from qcodes.utils.validators import Numbers, MultiType, Ints 
from measurements.Protocols import Protocol
from typing import List, Dict, Any 




class T2EchoProtocol(Protocol):
    """
        This protocol initializes and runs a T2 ramsey measurement 
        program, and correctly formats the output into a desired form. 
    """
    def __init__(self, name="T2_Echo_Protocol"):
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

        self.add_parameter('variable_delay',
                            parameter_class=ManualParameter,
                            label='Variable delay between qubit excitation and readout',
                            vals = Numbers(*[0,4000]),
                            unit = 'us',
                            initial_value = 5)

        self.add_parameter('reps',
                            parameter_class=ManualParameter,
                            label='Measurement repetitions',
                            vals = Ints(0,5000),
                            initial_value = 400)
                            
        self.add_parameter('readout_pulse_delay',
                            parameter_class=ManualParameter,
                            label='Delay between ending the probe pulse and initiating the readout pulse',
                            vals = Numbers(*[0,1000]),
                            unit = 'us',
                            initial_value = 0.05)        

    def compile_hardware_sweep_dict(self, sweep_configuration, internal_variables, sweep_parameter_list ):
        """
        This can be hardcoded for now.
        """

        internal_config = {}
        internal_config["start"] = 0
        internal_config["expts"] = self.variable_delay.get()
        internal_config["step"] = 1 

        for parameter, values in sweep_configuration.items():
            if parameter == internal_variables['variable_delay']:
                internal_config["start"] = values[0]
                internal_config["expts"] = values[2]
                internal_config["step"] = (values[1]-values[0])/values[2]
                sweep_parameter_list = self.add_sweep_parameter(isHardware = True, parameter = parameter, sweep_parameter_list = sweep_parameter_list)

        return internal_config, sweep_parameter_list

    def initialize_qick_config(self, sweep_configuration):
        """ 
        Initialize the qick soc and qick config
        
        """

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

                    #For the T2 program, readout probe pulse
                    #lenght is a good readout lenght
                    'readout_length' : self.validated_IO['readout'].pulse_length,

                    #These are channel specific values 
                    'qubit_ch' : self.validated_IO['qubit'].channel,
                    'qubit_nqz' : self.validated_IO['qubit'].nqz,
                    'qubit_gain' : self.validated_IO['qubit'].pulse_gain,
                    'qubit_freq' : self.validated_IO['qubit'].pulse_freq,
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

        sweep_parameter_list = []
        external_config, sweep_parameter_list = self.compile_software_sweep_dict( sweep_configuration, external_parameters, sweep_parameter_list )

        # Internal parameters that can be swept in hardware
        internal_parameters = { 
                    'variable_delay' : self.variable_delay,
                   }

        internal_config, sweep_parameter_list = self.compile_hardware_sweep_dict(sweep_configuration, internal_parameters, sweep_parameter_list)
        qick_config = {**external_config, **internal_config}

        return qick_config, sweep_parameter_list

                
    def run_program(self, soc, cfg : Dict[str, float]):
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

        expt_pts, avg_i, avg_q = self.run_hybrid_loop_program(soc, self.cfg, T2EchoProgram)
        return expt_pts, avg_i, avg_q 

    def handle_output(self, expt_pts, avg_i, avg_q):
        """
        This method handles formatting the output into a standardized
        form, to be sent to back to the ZCU216Station. 

        Parameters:
            expt_pts:
                array of arrays containing each of the experiment
                values (only once) for each of the sweepable variables.
                This contains the coordinates of our measurement.
            avg_i: 
                I values of the measurement each corresponding to 
                a specific combination of coordinates. 
            avg_q: 
                Q values of the measurement each corresponding to 
                a specific combination of coordinates. 


        Returns:
            expt_pts: 
                list of N (coordinate amount) arrays whose each element
                corresponds to an individual measurement. Thus, the lists
                will be the same size as there are total measurement points
                and for each index you may find the corresponding coordinate
                point of an individual measurement from each of the arrays.
            avg_i: 
                In this method, the average i values are unchanged
            avg_q: 
                In this method, the average q values are unchanged
            
        """
        avg_i = avg_i[0]
        avg_i = avg_i.flatten()
        avg_q = avg_q[0]
        avg_q = avg_q.flatten()
        expt_pts = expt_pts.tolist()
        return [expt_pts], avg_i, avg_q 


class T2EchoProgram(RAveragerProgram):
    """
    NOTE: This program assumes that the pulse length given to the qubit channel is the 
          lenght of the pi/2 pulse, to make it more alike to the T2Ramsey protocol.
    
    """

    def initialize(self):
        cfg=self.cfg

        #Qubit refers to the probe pulse
        #ro refers to readout
        #Cavity refers to the low power resonant probe

        #Defining local variables for qubit probing and readout.
        #The channel for the qubit probing is the channel corresponding
        #to the default pulse variables (pulse_lenght, pulse_phase, etc.)
        qubit_ch = cfg["qubit_ch"]
        probe_gain = round(cfg["qubit_gain"])
        probe_length = self.us2cycles(cfg['qubit_length'], gen_ch=qubit_ch)
        probe_phase = self.deg2reg(cfg["qubit_phase"], gen_ch=qubit_ch)

        cavity_freq=self.freq2reg(cfg["cavity_freq"], gen_ch=cfg["cavity_ch"], ro_ch=cfg["ro_ch"]) # conver f_res to dac register value
        probe_freq=self.freq2reg(cfg["qubit_freq"], gen_ch=cfg["qubit_ch"])

        cavity_pulse_length = self.us2cycles(cfg['readout_length'], gen_ch=cfg["cavity_ch"])

        #Get register page for qubit_ch
        self.q_rp=self.ch_page(qubit_ch)    
        self.r_variable_delay = 3
        self.regwi(self.q_rp, self.r_variable_delay, self.us2cycles(cfg["start"] / 2)) #divide by two since variable delay will represent the symmetric wait time between the three pulses

        self.declare_gen(ch=cfg["cavity_ch"], nqz=cfg["cavity_nqz"]) #Readout
        self.declare_gen(ch=cfg["qubit_ch"], nqz=cfg["qubit_nqz"]) #Qubit

        self.declare_readout(ch=cfg["ro_ch"], length=self.us2cycles(cfg["readout_length"]),
                             freq=cfg["cavity_freq"], gen_ch=cfg["cavity_ch"])


        # add readout pulses to respective channels
        #self.set_pulse_registers(ch=qubit_ch, style="const", freq=probe_freq, phase=probe_phase, gain=probe_gain, length=probe_length)
        self.set_pulse_registers(ch=cfg["cavity_ch"], style="const", freq=cavity_freq, phase=self.deg2reg(cfg["qubit_phase"], gen_ch=cfg["cavity_ch"]), gain=round(cfg["cavity_gain"]),
                                 length=cavity_pulse_length)

        self.sync_all(self.us2cycles(200))
        
    def body(self):
        
    
    
        #set pulse regs for pi/2 pulse
        self.set_pulse_registers( ch=self.cfg["qubit_ch"], style="const", freq=self.freq2reg(self.cfg["qubit_freq"], gen_ch=self.cfg["qubit_ch"]),
                                  phase= self.deg2reg(self.cfg["qubit_phase"], gen_ch=self.cfg["qubit_ch"]), gain=round(self.cfg["qubit_gain"]), length=self.us2cycles(self.cfg['qubit_length'], gen_ch=self.cfg["qubit_ch"]))
                                  
                                  
        #play  pi/2 qubit probe pulse    
        self.pulse(ch=self.cfg["qubit_ch"])  

        # Wait variable time tau / 2 
        self.sync_all()
        self.sync(self.q_rp, self.r_variable_delay)
        
        #set pulse regs for pi pulse
        self.set_pulse_registers( ch=self.cfg["qubit_ch"], style="const", freq=self.freq2reg(self.cfg["qubit_freq"], gen_ch=self.cfg["qubit_ch"]),
                                  phase= self.deg2reg(self.cfg["qubit_phase"], gen_ch=self.cfg["qubit_ch"]), gain=round(self.cfg["qubit_gain"]), length=self.us2cycles(2 * self.cfg['qubit_length'], gen_ch=self.cfg["qubit_ch"]))
        self.pulse(ch=self.cfg["qubit_ch"])  #play probe pulse
        


        # Wait variable time tau / 2
        self.sync_all()
        self.sync(self.q_rp, self.r_variable_delay)
        
        
        self.set_pulse_registers( ch=self.cfg["qubit_ch"], style="const", freq=self.freq2reg(self.cfg["qubit_freq"], gen_ch=self.cfg["qubit_ch"]),
                                  phase= self.deg2reg(self.cfg["qubit_phase"], gen_ch=self.cfg["qubit_ch"]), gain=round(self.cfg["qubit_gain"]), length=self.us2cycles(self.cfg['qubit_length'], gen_ch=self.cfg["qubit_ch"]))
        
        # play  pi/2 qubit probe pulse 
        self.pulse(ch=self.cfg["qubit_ch"])  #play probe pulse
        
        self.sync_all(self.us2cycles(self.cfg["readout_pulse_delay"]))

        #trigger measurement, play measurement pulse, wait for qubit to relax
        self.measure(pulse_ch=self.cfg["cavity_ch"], 
             adcs=[self.cfg["ro_ch"]],
             adc_trig_offset=round(self.cfg["adc_trig_offset"]),
             wait=True,
             syncdelay=self.us2cycles(self.cfg["relax_delay"]))
        
    def update(self):
        self.mathi(self.q_rp, self.r_variable_delay, self.r_variable_delay, '+', self.us2cycles(self.cfg["step"] / 2)) # update the time between two π/2 pulses

