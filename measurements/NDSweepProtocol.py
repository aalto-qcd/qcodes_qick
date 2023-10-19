import qcodes as qc
import numpy as np
import itertools
from qick import *
from qcodes.instrument import Instrument, ManualParameter
from qcodes.utils.validators import Numbers, MultiType, Ints 
from measurements.Protocols import Protocol
from typing import List, Dict, Any 




class NDSweepProtocol(Protocol):
    """
        This protocol initializes and runs a pulse probe spectroscopy measurement 
        program, and correctly formats the output into a desired form. 
    """
    def __init__(self, name="NDS_Protocol"):
        """
        Initialize the protocol object.
            
        """
        super().__init__(name)

        self.required_DACs = {'probe': 'Probe channel' }
        self.required_ADCs = {'adc' : 'Readout adc channel' }
        self.validated_IO = {'probe': None, 'adc': None}

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

        self.add_parameter('readout_length',
                            parameter_class=ManualParameter,
                            label='Lenght of the readout',
                            vals = Numbers(*[0,150]),
                            unit = 'us',
                            initial_value = 5)

        self.add_parameter('reps',
                            parameter_class=ManualParameter,
                            label='Measurement repetitions',
                            vals = Ints(0,5000),
                            initial_value = 400)

    def compile_hardware_sweep_dict(self, sweep_configuration, internal_variables):
        """
        This can be hardcoded for now.
        """

        internal_config = {}
        internal_config["start"] = self.validated_IO['qubit'].pulse_length.get()
        internal_config["expts"] = 1
        internal_config["step"] = 0 

        for parameter, values in sweep_configuration.items():
            if parameter == internal_variables['qubit_freq']:
                internal_config["start"] = values[0]
                internal_config["expts"] = values[2]
                internal_config["step"] = (values[1] - values[0])/values[2]

        return internal_config

    def initialize_qick_program(self, soc, sweep_configuration):
        """ 
        Initialize the qick soc and qick config
        
        """
        self.soc = soc

        #This is the only part where you need to hard code the qick config dictionary, this
        #is due to the fact that the qick config dictionary expect certain hard coded entries.
         
        # (Protocol specific) config corresponding to parameters that can only be swept outside of 
        # the qick program hardware loop
        external_parameters = { 
                    #These are protocol specific, inherent parameter values
                    'reps' : self.reps,
                    'relax_delay' : self.relax_delay,
                    'adc_trig_offset' : self.adc_trig_offset,
                    'readout_length' : self.readout_length,

                    #These are channel specific values 
                    'probe_ch' : self.validated_IO['probe'].channel,
                    'ro_ch' : self.validated_IO['adc'].channel,
                    'probe_nqz' : self.validated_IO['probe'].nqz,
                   }

        external_config = self.compile_software_sweep_dict( sweep_configuration, external_parameters )

        # Internal parameters that can be swept in hardware
        internal_parameters = { 
                    'qubit_freq' : self.validated_IO['probe'].pulse_freq,
                    'probe_gain' : self.validated_IO['probe'].pulse_gain,
                    'probe_phase' : self.validated_IO['probe'].pulse_phase,
                    'probe_length' : self.validated_IO['probe'].pulse_length,
                   }

        internal_config = self.compile_hardware_sweep_dict(sweep_configuration, internal_parameters)
        qick_config = {**external_config, **internal_config}

        return qick_config

                
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
        iterators = {}

        for parameter_name, value in self.cfg.items():
            if type(value) == list:
                iterators[parameter_name] = np.linspace(value[0],value[1],value[2]).tolist()

        expt_pts, avg_i, avg_q = self.run_hybrid_loop_program(self.cfg, PulseProbeSpectroscopyProgram, iterators)
        return expt_pts, avg_i, avg_q 


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

        #defining local variables.
        probe_ch = cfg["probe_ch"]
        freq = self.freq2reg(cfg["probe_freq"], gen_ch=probe_ch, ro_ch=cfg["ro_ch"])
        phase = self.deg2reg(cfg["probe_phase"], gen_ch=probe_ch)
        gain = cfg["probe_gain"]
        length = self.us2cycles(cfg['probe_length'], gen_ch=self.cfg['probe_ch'])
        sweep_variables = cfg["sweep_variables"]

        #Declare signal generators and readout
        self.declare_gen(ch=cfg["probe_ch"], nqz=cfg["nqz"], ro_ch=cfg["ro_ch"])
        self.declare_readout(ch=cfg["ro_ch"], length=self.us2cycles(self.cfg['readout_length'], ro_ch = self.cfg['ro_ch']),
                             freq=self.cfg["probe_freq"], gen_ch=cfg["probe_ch"])

        self.set_pulse_registers(ch=probe_ch, style="const", freq=freq, phase=phase, gain=gain, length=length)

        for sweep_variable in sweep_variables:
            if sweep_variable == "probe_length":
                
                #Getting the gen manager for calculating the correct start and end points of the mode register.
                #Thus, by utilizing these methods you may ensure that you will not sent an improper mode register.
                gen_manager = FullSpeedGenManager(self, cfg["probe_ch"]) 
                sweep_settings = sweep_variables[sweep_variable]
                start_length = self.us2cycles(sweep_settings[0])
                end_length = self.us2cycles(sweep_settings[1])
                start_code = gen_manager.get_mode_code(length=start_length, outsel="dds")
                end_code = gen_manager.get_mode_code(length=end_length, outsel="dds")

                #The register containing the pulse length as the last 16 bits is referred to as the "mode" register.
                sweep_register = self.get_gen_reg(cfg["probe_ch"], "mode")
                self.add_sweep(QickSweep(self, sweep_register, start_code, end_code, sweep_settings[2]))
            else:
                sweep_settings = sweep_variables[sweep_variable]
                sweep_register = self.get_gen_reg(cfg["probe_ch"], sweep_variable.replace('probe_', ''))
                self.add_sweep(QickSweep(self, sweep_register, sweep_settings[0], sweep_settings[1], sweep_settings[2]))


        self.synci(200)  #Give processor some time to configure pulses

    def body(self):
        """
            The main structure of the measurement is just the measurement,
            but the add_sweep commands in the initialize method add inner loops
            into the qick program instructions.
        """

        self.measure(pulse_ch=self.cfg["probe_ch"],
                     adcs=[self.cfg["ro_ch"]],
                     pins=[0],
                     adc_trig_offset=self.cfg["adc_trig_offset"],
                     wait=True,
                     syncdelay=self.us2cycles(self.cfg["relax_delay"]))

