import qcodes as qc
from qcodes.instrument import Instrument, ManualParameter
from qcodes.station import Station
from qcodes.utils.validators import Numbers, MultiType, Ints 
from qick import *
from qick.averager_program import QickSweep
from multi_variable_sweep import MultiVariableSweepProgram
import numpy as np


class ZCU216MetaInstrument(Instrument):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.soc = QickSoc()


        #The following parameters contain all QickConfig parameters
        #that the user may modify before running the specific
        #experiment, and the parameters that may be looped over in the program. 

        self.add_parameter('reps',
                            parameter_class=ManualParameter,
                            label='Measurement repetitions',
                            vals = Ints(0,5000))
        self.add_parameter('relax_delay',
                            parameter_class=ManualParameter,
                            label='Measurement repetitions',
                            vals = Numbers(*[0,500e6]),
                            unit = 'us')
        self.add_parameter('adc_trig_offset',
                            parameter_class=ManualParameter,
                            label='ADC trigger offset',
                            vals = Numbers(*[0,500e6]),
                            unit = 'us')
        self.add_parameter('soft_avgs',
                            parameter_class=ManualParameter,
                            label='Soft averages',
                            vals = Ints(0,5000))
        self.add_parameter('gain',
                            parameter_class=ManualParameter,
                            label='DAC gain',
                            vals = Numbers(*[0,5e9]),
                            unit = 'DAC units')
        self.add_parameter('qubit_ch',
                            parameter_class=ManualParameter,
                            label='Qubit probe channel',
                            vals = Ints(0,6))
        self.add_parameter('res_ch',
                            parameter_class=ManualParameter,
                            label='Readout channel',
                            vals = Ints(0,1))




        self.add_parameter('freq',
                            parameter_class=ManualParameter,
                            label='DAC frequency',
                            vals = Numbers(*[0,500e3]),
                            unit = 'MHz')
        
        self.add_parameter('phase',
                            parameter_class=ManualParameter,
                            label='Pulse phase',
                            vals = Ints(0,360),
                            unit = 'deg')

        self.add_parameter('length',
                            parameter_class=ManualParameter,
                            label='Pulse length',
                            vals = Ints(3, 65536),
                            unit = 'Clock cycles')

        #Default values for standard options (propably not too good right now)
        self.reps(1)
        self.relax_delay(self.soc.us2cycles(0.01))
        self.adc_trig_offset(170)
        self.soft_avgs(1)
        self.qubit_ch(6)
        self.res_ch(0)



    def generate_config(self):

        default_config = {}

        # generate a configuration dict based on self.parameters
        for config_parameter in self.parameters:
            if config_parameter != "IDN" and self.get(config_parameter) != None:
                default_config[config_parameter] = self.get(config_parameter)
                
            
        return default_config

class ZCU216Station(Station):

    def initialize_qick_program(self, sweep_configuration, qicksoc, config):
        '''
        This function handles input validation and initializing qcodes around the actual measurement.
        It also handles the proper initialization of the config that will be given to a Qick program
        that is called here.

                Parameters:
                        sweep_configuration (dict): Dictionary that contains the sweep variables
                                                    characterized by their flag as their key,
                                                    and their sweep start value, end value and
                                                    step amount as a list as the dict value.

                        soc: The actual QickSoc object. 
                        soccfg: In this case soccfg and soc point to the same object. If using
                        pyro4, then soc is a Proxy object and soccfg is a QickConfig object.
        '''


        iq_config = {
                  "length": 100,  # [Clock ticks]
                  "readout_length": 100,  # [Clock ticks]
                  "pulse_freq": 100,  # [MHz]
                  "pulse_gain": 10000,  # [DAC units]
                  "pulse_phase": 0,  # [MHz]
                  "sweep_variables": sweep_configuration
              }

        zcu_config = {**config, **iq_config}
        prog = MultiVariableSweepProgram(qicksoc, zcu_config)

        return prog

    #dimension will refer to the amount dimension of the sweep in the program
    #Set up the QCoDeS experiment setup

    def measure_iq( self,  params_and_values ):

        # this config stays constant for the whole measurement
        zcu_config = self.zcu.generate_config()

        experiment = qc.load_or_create_experiment( experiment_name="zcu_qcodes_test", sample_name="iq_measure")
        meas = qc.Measurement(exp=experiment)

        dimension = 0
        sweep_param_objects = []
        possible_sweep_params = {"freq":"MHz", "gain":"DAC units", "phase":"deg", "length":"us"}
        sweep_configuration = {}

        for parameter in params_and_values:
            sweep_configuration[parameter.name] = params_and_values[parameter]

        #Create manual parameters for gathering data
        for sweepable_variable in sweep_configuration:

            #Check wether we can actually loop over each parameter
            if sweepable_variable  not in possible_sweep_params.keys():
                print("Invalid sweep parameter")
                return

            #Deifne the manual parameters
            sweep_param_object = qc.ManualParameter(sweepable_variable, 
                    instrument = None, unit=possible_sweep_params[sweepable_variable],
                    initial_value = sweep_configuration[sweepable_variable][0])

            dimension += 1
            sweep_param_objects.append(sweep_param_object)
            meas.register_parameter(sweep_param_object)
    

        #Define the custom parameters which are dependent on the manual parameters
        meas.register_custom_parameter("avg_i", setpoints=sweep_param_objects)
        meas.register_custom_parameter("avg_q", setpoints=sweep_param_objects)

        sweep_param_objects.reverse()
        param_values = []

        with meas.run() as datasaver:

            #Problem with getting this param
            prog = self.initialize_qick_program(sweep_configuration, self.zcu.soc, zcu_config)
    
            print(prog)

            #The actual qick measurement happens here, as defined by the program
            expt_pts, avg_i, avg_q = prog.acquire(self.zcu.soc, load_pulses=True)
    
            #Create tuples containing 1D data of each experiment point of each sweeped variable
            for i in range(dimension):
                param_values.append((sweep_param_objects[i], expt_pts[i]))
    
            #Get rid of unnecessary outer brackets.
            for i in range(avg_i.ndim-dimension):
                avg_i = np.squeeze(avg_i)
                avg_q = np.squeeze(avg_q)

            
    
            datasaver.add_result( ("avg_i", avg_i), ("avg_q", avg_q), *param_values)

        run_id = datasaver.dataset.captured_run_id
        dataset = datasaver.dataset
        return run_id

qc.initialise_or_create_database_at("./zcu_test_data.db")

station = ZCU216Station()
station.add_component(ZCU216MetaInstrument(name="zcu"))



print(station.zcu.print_readable_snapshot())

run_id = station.measure_iq(params_and_values = {station.zcu.freq: [80, 120, 200]})


