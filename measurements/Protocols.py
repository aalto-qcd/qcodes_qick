import qcodes as qc
import numpy as np
import itertools
from qick import *
from qcodes.instrument import InstrumentBase, ManualParameter
from qcodes.utils.validators import Numbers, MultiType, Ints 


class Protocol(InstrumentBase):
    """
    The protocol class is a wrapper around an actual qick program, which
    handles initializing and running the qick program, and handling output
    into the correct form desired by the ZCUStation. Each protocol corresponds
    to a specific qick program.
    """
    def __init__(self, name, label):
        super().__init__(name=name, label=label)
        self.required_DACs = {}
        self.required_ADCs = {}
        self.validated_IO = {}

        pass

    def initialize_qick_program(self, soc, sweep_configuration):
        """ 
        Abstract method for possible initialization functionality 

        """
        pass

    def run_program(self):
        """ 
        Abstract method for running the program and returning th
        measurement result in the correct form.

        """
        pass

    def handle_output(self):
        """ 
        Abstract method for handling the output into the correct form 

        """
        pass

    def compile_hardware_sweep_dict( self, sweep_configuration : dict[qc.Parameter, list],  external_parameters : dict[str, qc.Parameter]):
        """
        This can one day be such that you can sweep all 
        hardware sweepable variables through calling this
        """

        pass



    def set_io(self, io_data : dict[str, qc.Instrument]):

        temp_IO = self.validated_IO.copy()
        
        for io_port in io_data.keys():
            if io_data[io_port].isDAC and io_port in self.required_DACs:
                temp_IO[io_port] = io_data[io_port]

            elif io_data[io_port].isADC and io_port in self.required_ADCs:
                temp_IO[io_port] = io_data[io_port]

            else:
                raise Exception("Invalid IO channel: " + io_port)
                return False
        
        for io_port in self.validated_IO:
            if io_port is None:
                self.validated_IO = {}
                raise Exception("Invalid IO channel: " + io_port)
                return False
        else:
            self.validated_IO = temp_IO
            return True


    def validate_params(self, params_and_values : dict[qc.Parameter, list]):
        #Validate params and values
        #This is only an elementary check. We want to be able to trust
        #That the iteration list corresponding to the parameter is valid
        for parameter, sweep_configuration in params_and_values.items():
            if parameter.validate(sweep_configuration[0]) is None and parameter.validate(sweep_configuration[0]) is None:
                pass
            else:
                raise Exception("Invalid parameter setpoints: " + parameter.name )
                return False
        return True 
            
    def compile_software_sweep_dict( self, sweep_configuration : dict[qc.Parameter, list],  external_parameters : dict[str, qc.Parameter]):

        external_parameter_config = {}

        for config_key, parameter in external_parameters.items():
            if parameter in sweep_configuration.keys():
                external_parameter_config[config_key] = sweep_configuration[parameter]
            else:
                external_parameter_config[config_key] = parameter.get()

        return external_parameter_config
             




    



class T1Protocol(Protocol):
    """
        This protocol initializes and runs a T1 decay measurement 
        program, and correctly formats the output into a desired form. 
    """
    def __init__(self, name="T1_Protocol"):
        """
        Initialize the protocol object.
            
        """
        super().__init__(name=name, label="T1 Decay Protocol Object")

        self.required_DACs = {'qubit': 'Qubit probe channel', 'readout' : 'Readout pulse channel', }
        self.required_ADCs = {'adc' : 'Readout adc channel' }
        self.validated_IO = {'qubit' : None, 'qubit': None, 'qubit': None}

        self.sensible_defaults = {
                                   "adc_trig_offset"  : 100,    # -- Clock ticks
                                   "relax_delay"      : 1,      # -- us 
                                   "t1_sigma"         : 0.025,  # -- us
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

        self.add_parameter('t1_sigma',
                            parameter_class=ManualParameter,
                            label='Standard deviation of gaussian',
                            vals = Numbers(*[0,4000]),
                            unit = 'us',
                            initial_value = 0.025)

        self.add_parameter('variable_delay',
                            parameter_class=ManualParameter,
                            label='Variable delay between qubit excitation and readout',
                            vals = Ints(*[0,4000]),
                            unit = 'us',
                            initial_value = 500)

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
        if 'variable_delay' in sweep_configuration:
            internal_config["start"] = sweep_configuration["variable_delay"][0]
            internal_config["expts"] = sweep_configuration["variable_delay"][2]
            internal_config["step"] = (sweep_configuration["variable_delay"][1] 
                                       - sweep_configuration["variable_delay"][0])/sweep_configuration["variable_delay"][2]
        else:
            internal_config["start"] = 0
            internal_config["expts"] = self.variable_delay.get()
            internal_config["step"] = 1 

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
                    't1_sigma' : self.t1_sigma,
                    'relax_delay' : self.relax_delay,
                    'adc_trig_offset' : self.adc_trig_offset,

                    #For the T1 program, readout probe pulse
                    #lenght is a good readout lenght
                    'readout_lenght' : self.validated_IO['readout'].pulse_length,

                    #These are channel specific values 
                    'qubit_ch' : self.validated_IO['qubit'].channel,
                    'cavity_ch' : self.validated_IO['readout'].channel,
                    'ro_ch' : self.validated_IO['adc'].channel,
                    'qubit_nqz' : self.validated_IO['qubit'].nqz,
                    'cavity_nqz' : self.validated_IO['readout'].nqz,
                    'qubit_gain' : self.validated_IO['qubit'].pulse_gain,
                    'cavity_gain' : self.validated_IO['readout'].pulse_gain,
                    'qubit_freq' : self.validated_IO['qubit'].pulse_freq,
                    'cavity_freq' : self.validated_IO['readout'].pulse_freq,
                    'qubit_phase' : self.validated_IO['qubit'].pulse_phase,
                    'cavity_phase' : self.validated_IO['readout'].pulse_phase,
                    'qubit_phase' : self.validated_IO['qubit'].pulse_phase,
                    'cavity_phase' : self.validated_IO['readout'].pulse_phase,
                    'qubit_length' : self.validated_IO['qubit'].pulse_length,
                    'cavity_length' : self.validated_IO['readout'].pulse_length
                   }

        external_config = self.compile_software_sweep_dict( sweep_configuration, external_parameters )

        # Internal parameters that can be swept in hardware
        internal_parameters = { 
                    'variable_delay' : self.variable_delay,
                   }

        internal_config = self.compile_hardware_sweep_dict(sweep_configuration, internal_parameters)
        qick_config = {**external_config, **internal_config}

        return qick_config

                
    def run_program(self):
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
        #prog = T1Program(self.soccfg, self.cfg)
        #Dumb data
        expt_pts = np.array([400, 500])        
        avg_i = [np.array([[-0.02673513, -0.02834141]])]
        avg_q = [np.array([[0.08327843, 0.08439062]])]

        #expt_pts, avg_i, avg_q = prog.acquire(self.soccfg, load_pulses=True, progress=True)
        expt_pts, avg_i, avg_q = self.handle_output(expt_pts, avg_i, avg_q)


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


class T1Program(RAveragerProgram):
    def initialize(self):
        cfg=self.cfg

        #Qubit refers to the probe pulse
        #Res refers to readout
        #Cavity refers to the low power resonant probe

        #Defining local variables for qubit probing and readout.
        #The channel for the qubit probing is the channel corresponding
        #to the default pulse variables (pulse_lenght, pulse_phase, etc.)
        qubit_ch = cfg["qubit_ch"]
        probe_gain = cfg["pulse_gain"]
        probe_length = self.us2cycles(cfg['pulse_length'], gen_ch=qubit_ch)

        cavity_freq=self.freq2reg(cfg["cavity_freq"], gen_ch=cfg["cavity_ch"], ro_ch=cfg["res_ch"]) # conver f_res to dac register value
        probe_freq=self.freq2reg(cfg["pulse_freq"], gen_ch=cfg["qubit_ch"])

        t1_sigma = self.us2cycles(cfg["t1_sigma"], qubit_ch)
        cavity_pulse_length = self.us2cycles(cfg['readout_length'], gen_ch=cfg["cavity_ch"])

        #Get the start and step count of the relax delay sweep
        time_sweep = cfg["sweep_variables"]["delay_time"]
        cfg["expts"] = time_sweep[2]
        cfg["start"] = time_sweep[0]
        step_size = (time_sweep[1]-time_sweep[0])/time_sweep[2]
        cfg["step"] = step_size

        #Get register page for qubit_ch
        self.q_rp=self.ch_page(qubit_ch)    
        self.r_wait = 3
        self.regwi(self.q_rp, self.r_wait, self.us2cycles(cfg["start"]))

        self.declare_gen(ch=cfg["cavity_ch"], nqz=1) #Readout
        self.declare_gen(ch=cfg["qubit_ch"], nqz=cfg["nqz"]) #Qubit

        self.declare_readout(ch=cfg["res_ch"], length=self.us2cycles(cfg["readout_length"]),
                             freq=cfg["cavity_freq"], gen_ch=cfg["cavity_ch"])


        # add qubit and readout pulses to respective channels
        self.add_gauss(ch=qubit_ch, name="qubit", sigma=t1_sigma, length=t1_sigma*4)
        self.set_pulse_registers(ch=qubit_ch, style="arb", freq=probe_freq, phase=0, gain=probe_gain,
                                 waveform="qubit")
        self.set_pulse_registers(ch=cfg["cavity_ch"], style="const", freq=cavity_freq, phase=cfg["cavity_phase"], gain=cfg["cavity_gain"],
                                 length=cavity_pulse_length)

        self.sync_all(self.us2cycles(500))

    def body(self):

        #Probe the qubit with the gaussian pulse
        self.pulse(ch=self.cfg["qubit_ch"])  
        self.sync_all()

        #Variable wait time is applied here
        self.sync(self.q_rp,self.r_wait)

        #trigger measurement, play measurement pulse, wait for qubit to relax
        self.measure(pulse_ch=self.cfg["cavity_ch"],
             adcs=[self.cfg["res_ch"]],
             adc_trig_offset=self.cfg["adc_trig_offset"],
             wait=True,
             syncdelay=self.us2cycles(self.cfg["relax_delay"]))

    def update(self):
        self.mathi(self.q_rp, self.r_wait, self.r_wait, '+', self.us2cycles(self.cfg["step"])) # update variable delay
 
