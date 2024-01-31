import qcodes as qc
import numpy as np
import itertools
from qick import *
from qick.averager_program import QickSweep
from qcodes.instrument import Instrument, ManualParameter
from qcodes.utils.validators import Numbers, MultiType, Ints 
from measurements.Protocols import Protocol
from typing import List, Dict, Any 


from tqdm.auto import tqdm



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
                            label='Delay between sending probe pulse and ADC initialization',
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

        sweep_config = {}
        internal_config = {}
        for config_name, parameter in internal_variables.items():
            if parameter in sweep_configuration.keys():
                values = sweep_configuration[parameter]
                sweep_config[config_name] = [ values[0], values[-1], (values[-1]-values[0])/len(values)]
                internal_config[config_name] = values[0] 
                self.add_sweep_parameter(isHardware = True, parameter = parameter)
            else:
                internal_config[config_name] = parameter.get() 



        internal_config["sweep_variables"] = sweep_config

        return internal_config

    def initialize_qick_program(self, soc, soccfg, sweep_configuration):

        """ 
        Initialize the qick soc and qick config
        NOTE: soc is the Pyro4 proxy object, and soccfg is a QickConfig object inferred from the proxy object
        
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
                    'readout_length' : self.readout_length,

                    #These are channel specific values 
                    'probe_ch' : self.validated_IO['probe'].channel,
                    'ro_ch' : self.validated_IO['adc'].channel,
                    'probe_nqz' : self.validated_IO['probe'].nqz,
                    'probe_freq' : self.validated_IO['probe'].pulse_freq,
                   }

        external_config = self.compile_software_sweep_dict( sweep_configuration, external_parameters )

        # Internal parameters that can be swept in hardware
        internal_parameters = { 
                    'probe_gain' : self.validated_IO['probe'].pulse_gain,
                    'probe_phase' : self.validated_IO['probe'].pulse_phase,
                    'probe_length' : self.validated_IO['probe'].pulse_length,
                   }

        internal_config = self.compile_hardware_sweep_dict(sweep_configuration, internal_parameters)

        qick_config = {**external_config, **internal_config}

        return qick_config, self.sweep_parameter_list

                
    def run_program(self, cfg : Dict[str, float]):
        """
        This method runs the program and returns the measurement 
        result. For the NDSweep program, combining both multiple
        hardware sweeps and software sweeps, this method is implemented
        fully in the protocol. For RAveragerprograms, see Protocol.run_hybrid_loop_program

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
        software_iterators = {}
        iterations = 1
        

        for parameter_name, value in cfg.items():
            if type(value) == list:
                software_iterators[parameter_name] = value.tolist()
                iterations = iterations*(len(value))


        if len(software_iterators) == 0:
            program = HardwareSweepProgram(self.soccfg, cfg)
            expt_pts, avg_i, avg_q = program.acquire(self.soc, progress=True)
            expt_pts, avg_i, avg_q = self.handle_hybrid_loop_output(expt_pts, avg_i, avg_q)
            for i in range(len(list(cfg['sweep_variables']))):
                if list(cfg['sweep_variables'])[i] == 'probe_length':
                    length_expt_pts = expt_pts[i]
                    mode_code = length_expt_pts[0] - self.soc.us2cycles(cfg['sweep_variables']['probe_length'][0])
                    f = lambda x: self.soc.cycles2us(x - mode_code)
                    fixed_length_vals = [ f(x) for x in length_expt_pts]
                    expt_pts[i] = fixed_length_vals
                    

            for i in range(avg_i.ndim-len(cfg['sweep_variables'])):
                avg_i = np.squeeze(avg_i.flatten())
                avg_q = np.squeeze(avg_q.flatten())

            return expt_pts, avg_i, avg_q


        else:

            iteratorlist = list(software_iterators)
            hardware_loop_dim = len((cfg['sweep_variables']))


            total_hardware_sweep_points = 1
            for sweep_var in cfg['sweep_variables']:
                total_hardware_sweep_points = total_hardware_sweep_points*cfg['sweep_variables'][sweep_var][2]
            

            software_expt_data = [ [] for i in range(len(software_iterators))]
            hardware_expt_data = [ [] for i in range(hardware_loop_dim)]
            i_data = []
            q_data = []

            for coordinate_point in tqdm(itertools.product(*list(software_iterators.values())), total=iterations):

                for coordinate_index in range(len(coordinate_point)):
                    cfg[iteratorlist[coordinate_index]] = coordinate_point[coordinate_index]


                program = HardwareSweepProgram( self.soccfg, cfg )
                expt_pts, avg_i, avg_q = program.acquire(self.soc )

                for i in range(hardware_loop_dim):
                    if list(cfg['sweep_variables'])[i] == 'probe_length':
                        length_expt_pts = expt_pts[i]
                        mode_code = length_expt_pts[0] - self.soc.us2cycles(cfg['sweep_variables']['probe_length'][0])
                        f = lambda x: self.soc.cycles2us(x - mode_code)
                        fixed_length_vals = [ f(x) for x in length_expt_pts]
                        expt_pts[i] = fixed_length_vals
                    else:
                        expt_pts[i] = expt_pts[i].tolist()

                expt_pts, avg_i, avg_q = self.handle_hybrid_loop_output(expt_pts, avg_i, avg_q)

                i_data.extend(avg_i.flatten()) 
                q_data.extend(avg_q.flatten()) 

                for i in range(hardware_loop_dim):
                    hardware_expt_data[i].extend(expt_pts[i])
                for i in range(len(software_iterators)):
                    software_expt_data[i].extend([ coordinate_point[i] for x in range(total_hardware_sweep_points) ])

        
        software_expt_data.reverse()
        software_expt_data.extend(hardware_expt_data)

        return software_expt_data, i_data, q_data


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
        length = self.us2cycles(cfg['probe_length'], gen_ch=cfg['probe_ch'])
        sweep_variables = cfg["sweep_variables"]

        #Declare signal generators and readout
        self.declare_gen(ch=cfg["probe_ch"], nqz=cfg["probe_nqz"], ro_ch=cfg["ro_ch"])
        self.declare_readout(ch=cfg["ro_ch"], length=self.us2cycles(cfg['readout_length'], ro_ch = cfg['ro_ch']),
                             freq=cfg["probe_freq"], gen_ch=cfg["probe_ch"])

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
        cfg = self.cfg

        self.measure(pulse_ch=cfg["probe_ch"],
                     adcs=[cfg["ro_ch"]],
                     pins=[0],
                     adc_trig_offset=round(cfg["adc_trig_offset"]),
                     wait=True,
                     syncdelay=self.us2cycles(cfg["relax_delay"]))

