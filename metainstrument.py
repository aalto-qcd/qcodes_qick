import qcodes as qc
from qcodes.instrument import Instrument, ManualParameter
from qcodes.station import Station
from qcodes.utils.validators import Numbers, MultiType, Ints 
from qick import *
from qick.averager_program import QickSweep
from protocols import Protocol, NDSweepProtocol 
import numpy as np


class ZCU216MetaInstrument(Instrument):
    '''
    This class is an abstract QCoDes instrument, which
    contains the settable and gettable parameters of the zcu216, most of which
    correspond to configuration variables in the qick program config dictionary. 
    '''

    def __init__(self, name, **kwargs):
        '''
        As we initialize the metainstrument, each of the gettable and settable 
        parameters are defined, and some of them initialized. Parameters that
        are specific to a certain measurement do not receive an initial value.
        Other parameters will have set initial values, that the user may 
        configure before performing a measurement.
        '''

        super().__init__(name, **kwargs)

        self.soc = QickSoc()


        #The following parameters contain all QickConfig parameters
        #that the user may modify before running the specific
        #experiment, and the parameters that may be looped over in the program. 
        #These have some "sensible" default values.

        self.add_parameter('reps',
                            parameter_class=ManualParameter,
                            label='Measurement repetitions',
                            vals = Ints(0,5000),
                            initial_value = 100)

        self.add_parameter('relax_delay',
                            parameter_class=ManualParameter,
                            label='Measurement repetitions',
                            vals = Numbers(*[0,500e6]),
                            unit = 'us',
                            initial_value = 0.1)

        self.add_parameter('adc_trig_offset',
                            parameter_class=ManualParameter,
                            label='ADC trigger offset',
                            vals = Numbers(*[0,500e6]),
                            unit = 'us',
                            initial_value = 0.1)
        self.add_parameter('soft_avgs',
                            parameter_class=ManualParameter,
                            label='Soft averages',
                            vals = Ints(0,5000),
                            initial_value = 1)
        self.add_parameter('qubit_ch',
                            parameter_class=ManualParameter,
                            label='Qubit probe channel',
                            vals = Ints(0,6),
                            initial_value = 6)
        self.add_parameter('res_ch',
                            parameter_class=ManualParameter,
                            label='Readout channel',
                            vals = Ints(0,1),
                            initial_value = 0)
        self.add_parameter('nqz',
                            parameter_class=ManualParameter,
                            label='Nyquist zone',
                            vals = Ints(1,2),
                            initial_value = 1)



        #Measurement specific settings, that do not receive an initial value
        self.add_parameter('gain',
                            parameter_class=ManualParameter,
                            label='DAC gain',
                            vals = Numbers(*[0,5e9]),
                            unit = 'DAC units')
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




    def generate_config(self):
        """
        In this function, we generate a qick configuration dictionary based
        on the parameters in the metainstrument, which the user may have set
        before running a measurement.

        return: qick configuration dict
        """

        default_config = {}

        # generate a configuration dict based on self.parameters
        for config_parameter in self.parameters:
            if config_parameter != "IDN" and self.get(config_parameter) != None:
                default_config[config_parameter] = self.get(config_parameter)
                
            
        return default_config

class ZCU216Station(Station):
    '''
    This class is an abstract QCoDes station, which handles the configuration,
    initialization and execution of a measurement using the zcu216. It also
    enables the saving of the measurement results using QCoDes into a database.

    '''

    def initialize_qick_program(self, sweep_configuration, qicksoc, config, protocol):
        '''
        This function handles input validation and initializing qcodes around 
        the actual measurement. It also handles the proper initialization of 
        the program config that will be given to a Qick program that is called.

                Parameters:
                        sweep_configuration (dict): 
                        Dictionary that contains the sweep variables
                        characterized by their flag as their key,
                        and their sweep start value, end value and
                        step amount as a list as the dict value.

                        qicksoc: The actual QickSoc object. 
                        config: A qick program configuration dictionary
                        protocol: the protocol object used in the measurement

                return: protocol object
        '''


        iq_config = {
                  "length": 100,  # [Clock ticks]
                  "readout_length": 150,  # [Clock ticks]
                  "pulse_freq": 100,  # [MHz]
                  "pulse_gain": 10000,  # [DAC units]
                  "pulse_phase": 0,  # [MHz]
                  "sweep_variables": sweep_configuration
              }


        zcu_config = {**config, **iq_config}
        protocol.initialize_program(qicksoc, zcu_config)

        return protocol 


    def measure_iq( self,  params_and_values, protocol: Protocol ):
        '''
        This function initializes and runs an IQ measurement.

                Parameters:
                        params_and_values (dict): 
                        Dictionary that contains the sweep variables
                        as qcodes parameters, with keys being a list
                        containing the measurement start point, end point
                        and the step count.
                        protocol: the protocol object used in the measurement

                return: QCoDeS run id, corresponding to the measurement
                        (if succesful). 
        '''

        # this config stays constant for the whole measurement
        zcu_config = self.zcu.generate_config()

        # initialize qcodes
        experiment = qc.load_or_create_experiment( 
                experiment_name="zcu_qcodes_test", 
                sample_name=protocol.name)

        meas = qc.Measurement(exp=experiment)

        dimension = 0
        sweep_param_objects = []
        possible_sweep_params = {"freq":"MHz",
                                 "gain":"DAC units",
                                 "phase":"deg",
                                 "length":"us"}
        sweep_configuration = {}

        for parameter in params_and_values:
            sweep_configuration[parameter.name] = params_and_values[parameter]

        #Create manual parameters for gathering data
        for sweepable_variable in sweep_configuration:

            #Check wether we can actually loop over each parameter
            if sweepable_variable  not in possible_sweep_params.keys():
                print("Invalid sweep parameter")
                return

            #Define the manual parameters
            sweep_param_object = qc.ManualParameter(sweepable_variable, 
                    instrument = None,
                    unit=possible_sweep_params[sweepable_variable],
                    initial_value = sweep_configuration[sweepable_variable][0])

            dimension += 1
            sweep_param_objects.append(sweep_param_object)
            meas.register_parameter(sweep_param_object)
    

        #Define the custom parameters which are dependent on the manual parameters
        meas.register_custom_parameter("avg_i", setpoints=sweep_param_objects)
        meas.register_custom_parameter("avg_q", setpoints=sweep_param_objects)

        sweep_param_objects.reverse()
        param_values = []

        #The qcodes experiment, surrounding the qick program is contained here.
        with meas.run() as datasaver:

            #Initialize the 
            protocol = self.initialize_qick_program(sweep_configuration,
                                                    self.zcu.soc,
                                                    zcu_config,
                                                    protocol)

            #Run the qick program, as defined by the protocol and params_and_values
            expt_pts, avg_i, avg_q = protocol.run_program()

            #Divide the expt_pts array into individual measurement points
            #for each sweepable variable.
            for i in range(dimension):
                param_values.append((sweep_param_objects[i], expt_pts[i]))
    
            #Get rid of unnecessary outer brackets and flatten the matrix
            #into a list of measurement results.
            for i in range(avg_i.ndim-dimension):
                avg_i = np.squeeze(avg_i.flatten())
                avg_q = np.squeeze(avg_q.flatten())

            
    
            datasaver.add_result( ("avg_i", avg_i), ("avg_q", avg_q), *param_values)

        #Return the run_id
        run_id = datasaver.dataset.captured_run_id
        return run_id



