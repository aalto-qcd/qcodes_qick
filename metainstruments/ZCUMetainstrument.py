import qcodes as qc
from qcodes.instrument import Instrument, ManualParameter
from qcodes.station import Station
from qcodes.utils.validators import Numbers, MultiType, Ints 
from qick import *
from qick.averager_program import QickSweep
from measurements.protocols import Protocol, NDSweepProtocol, PulseProbeSpectroscopyProtocol, T1Protocol
import numpy as np


class ZCU216Metainstrument(Instrument):
    '''
    This class is an abstract QCoDes instrument, which
    contains the settable and gettable parameters of the zcu216, most of which
    correspond to configuration variables in the qick program config dictionary. 
    '''

    def __init__(self, name, **kwargs):
        '''
        As we initialize the metainstrument, each of the gettable and settable 
        parameters are defined and initialized. All parameters receive some
        initial value, but those that initial values corresponding to variables
        that are sweeped over are overwritten.
        '''

        super().__init__(name, **kwargs)

        #self.soc = QickSoc()
        self.soc = "QICK configuration:\n"+"\n"+" 	Board: ZCU216\n"+" \n"+" 	Software version: 0.2.211\n"+"  	Firmware timestamp: Mon Aug 21 11:09:34 2023\n"+"  \n"+"  	Global clocks (MHz): tProcessor 430.080, RF reference 245.760\n"+"  \n"+"  	7 signal generator channels:\n"+"  	0:	axis_signal_gen_v6 - envelope memory 65536 samples (9.524 us)\n"+"  		fs=6881.280 MHz, fabric=430.080 MHz, 32-bit DDS, range=6881.280 MHz\n"+"  		DAC tile 2, blk 0 is 0_230, on JHC3\n"+"  	1:	axis_signal_gen_v6 - envelope memory 65536 samples (9.524 us)\n"+"  		fs=6881.280 MHz, fabric=430.080 MHz, 32-bit DDS, range=6881.280 MHz\n"+"  		DAC tile 2, blk 1 is 1_230, on JHC4\n"+"  	2:	axis_signal_gen_v6 - envelope memory 65536 samples (9.524 us)\n"+"  		fs=6881.280 MHz, fabric=430.080 MHz, 32-bit DDS, range=6881.280 MHz\n"+"  		DAC tile 2, blk 2 is 2_230, on JHC3\n"+"  	3:	axis_signal_gen_v6 - envelope memory 65536 samples (9.524 us)\n"+"  		fs=6881.280 MHz, fabric=430.080 MHz, 32-bit DDS, range=6881.280 MHz\n"+"  		DAC tile 2, blk 3 is 3_230, on JHC4\n"+"  	4:	axis_signal_gen_v6 - envelope memory 65536 samples (9.524 us)\n"+"  		fs=6881.280 MHz, fabric=430.080 MHz, 32-bit DDS, range=6881.280 MHz\n"+"  		DAC tile 3, blk 0 is 0_231, on JHC3\n"+"  	5:	axis_signal_gen_v6 - envelope memory 65536 samples (9.524 us)\n"+"  		fs=6881.280 MHz, fabric=430.080 MHz, 32-bit DDS, range=6881.280 MHz\n"+"  		DAC tile 3, blk 1 is 1_231, on JHC4\n"+"  	6:	axis_signal_gen_v6 - envelope memory 65536 samples (9.524 us)\n"+"  		fs=6881.280 MHz, fabric=430.080 MHz, 32-bit DDS, range=6881.280 MHz\n"+"  		DAC tile 3, blk 2 is 2_231, on JHC3\n"+"  \n"+"  	2 readout channels:\n"+"  	0:	axis_readout_v2 - controlled by PYNQ\n"+"  		fs=2457.600 MHz, fabric=307.200 MHz, 32-bit DDS, range=2457.600 MHz\n"+"  		maxlen 16384 accumulated, 1024 decimated (3.333 us)\n"+"  		triggered by output 0, pin 14, feedback to tProc input 0\n"+"  		ADC tile 2, blk 0 is 0_226, on JHC7\n"+"  	1:	axis_readout_v2 - controlled by PYNQ\n"+"  		fs=2457.600 MHz, fabric=307.200 MHz, 32-bit DDS, range=2457.600 MHz\n"+"  		maxlen 16384 accumulated, 1024 decimated (3.333 us)\n"+"  		triggered by output 0, pin 15, feedback to tProc input 1\n"+"  		ADC tile 2, blk 2 is 2_226, on JHC7\n"+"  \n"+"  	8 digital output pins:\n"+"  	0:	PMOD0_0_LS\n"+"  	1:	PMOD0_1_LS\n"+"  	2:	PMOD0_2_LS\n"+"  	3:	PMOD0_3_LS\n"+"  	4:	PMOD0_4_LS\n"+"  	5:	PMOD0_5_LS\n"+"  	6:	PMOD0_6_LS\n"+"  	7:	PMOD0_7_LS\n"+"  \n"+"  	tProc axis_tproc64x32_x8: program memory 8192 words, data memory 4096 words\n"+"  		external start pin: PMOD1_0_LS\n"+"  \n"+"  	DDR4 memory buffer: 1073741824 samples (3.495 sec), 128 samples/transfer\n"+"  		wired to readouts [0, 1]\n"+"  \n"+"  	MR buffer: 8192 samples (3.333 us), wired to readouts [0, 1]\n"+" \n"

        self.validADCs = [0,1]
        self.validDACs = [0,1,2,3,4,5,6]

        self.sensible_defaults = { "reps" : 100,
                                   "relax_delay" : 0.1,
                                   "adc_trig_offset" : 1,
                                   "soft_avgs" : 1,
                                   "qubit_ch" : 6,
                                   "res_ch" : 0,
                                   "nqz" : 1,
                                   "readout_length" : 12,
                                   "pulse_gain" : 10000,
                                   "pulse_phase" : 0,
                                   "pulse_freq" : 500,
                                   "pulse_length" : 10 }

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
                            label='Relax delay',
                            vals = Numbers(*[0,1000000]),
                            unit = 'us',
                            initial_value = 0.1)

        self.add_parameter('adc_trig_offset',
                            parameter_class=ManualParameter,
                            label='ADC trigger offset',
                            vals = Ints(*[0,10000]),
                            unit = 'Clock ticks',
                            initial_value = 100)

        self.add_parameter('soft_avgs',
                            parameter_class=ManualParameter,
                            label='Soft averages',
                            vals = Ints(*[0,5000]),
                            initial_value = 1)

        self.add_parameter('qubit_ch',
                            parameter_class=ManualParameter,
                            label='Qubit probe channel',
                            vals = Ints(*[0,6]),
                            initial_value = 4)

        self.add_parameter('cavity_ch',
                            parameter_class=ManualParameter,
                            label='Cavity probe channel',
                            vals = Ints(*[0,6]),
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

        self.add_parameter('readout_length',
                            parameter_class=ManualParameter,
                            label='Lenght of the readout',
                            vals = Numbers(*[0,150]),
                            unit = 'us',
                            initial_value = 12)




        #Sweepable settings
        self.add_parameter('pulse_gain',
                            parameter_class=ManualParameter,
                            label='DAC gain',
                            vals = Numbers(*[0,40000]),
                            unit = 'DAC units',
                            initial_value = 10000)

        self.add_parameter('pulse_freq',
                            parameter_class=ManualParameter,
                            label='DAC frequency',
                            vals = Numbers(*[0,9000]),
                            unit = 'MHz',
                            initial_value = 500)
        
        self.add_parameter('pulse_phase',
                            parameter_class=ManualParameter,
                            label='Pulse phase',
                            vals = Ints(*[0,360]),
                            unit = 'deg',
                            initial_value = 0)

        self.add_parameter('pulse_length',
                            parameter_class=ManualParameter,
                            label='Pulse length',
                            vals = Numbers(*[0,150]),
                            unit = 'us',
                            initial_value = 10)

        #Cavity probe settings
        self.add_parameter('cavity_freq',
                            parameter_class=ManualParameter,
                            label='cavity probe pulse frequency',
                            vals = Numbers(*[0,9000]),
                            unit = 'MHz',
                            initial_value = 500)

        self.add_parameter('cavity_phase',
                            parameter_class=ManualParameter,
                            label='Cavity probe pulse phase',
                            vals = Ints(*[0,360]),
                            unit = 'deg',
                            initial_value = 0)

        self.add_parameter('cavity_gain',
                            parameter_class=ManualParameter,
                            label='Cavity probe dac gain',
                            vals = Numbers(*[0,40000]),
                            unit = 'DAC units',
                            initial_value = 10000)

        #T1 measurement stuff
        self.add_parameter('delay_time',
                            parameter_class=ManualParameter,
                            label='T1 variable delay',
                            vals = Numbers(*[0,10000]),
                            unit = 'us',
                            initial_value = 3)

        self.add_parameter('t1_sigma',
                            parameter_class=ManualParameter,
                            label='T1 variable delay',
                            vals = Numbers(*[0,10000]),
                            unit = 'us',
                            initial_value = 0.025)


    def add_DAC_channel(self, channel: int, name: str):
        if channel in self.validDACs:
            self.add_component(DACChannel(name = name, channel_number = channel))
        else:
            raise Exception("Invalid DAC channel number") 
            

    def add_ADC_channel(self, channel: int, name: str):
        if channel in self.validADCs:
            self.add_component(ADCChannel(name = name, channel_number = channel))
        else:
            raise Exception("Invalid ADC channel number") 

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
    
    def return_soc(self):
        """
        In this function, we generate a qick configuration dictionary based
        on the parameters in the metainstrument, which the user may have set
        before running a measurement.

        return: qick configuration dict
        """

                
        return self.soc

class ZCU216Station(Station):
    '''
    This class is an abstract QCoDes station, which handles the configuration,
    initialization and execution of a measurement using the zcu216. It also
    enables the saving of the measurement results using QCoDes into a database.

    '''
    def __init__(self):
        """
        Initialize the metainstrument
        """

        super().__init__()

        self.add_component(ZCU216MetaInstrument(name='zcu'))

    def troubleshoot(self):
        return self.zcu.return_soc()

    def set_original_defaults(self):
        """
        Set the original defaults
        """

        self.set_defaults(self.zcu.sensible_defaults)

    def set_defaults(self, defaults_dict):
        """
        This method configures new default for the station based on a dictionary
        with qcodes parameter names and their new default values
        """
        for parameter_name in defaults_dict:
            if parameter_name not in self.zcu.parameters:
                print(f"Unable to set default value for {parameter_name}; invalid parameter name")
            else:
                try:
                    param = self.zcu.parameters[parameter_name]
                    param.set(defaults_dict[parameter_name])
                except ValueError:
                    print(f"Unable to set default value for {parameter_name}; value outside of range {param.vals}")



    def validate_sweep(self, possible_sweep_params, parameter, sweep_list):
        '''
        This function handles input validation and initializing qcodes around 
        the actual measurement. It also handles the proper initialization of 
        the program config that will be given to a Qick program that is called.

                Parameters:
                        possible_sweep_params (dict): 
                            dictionary of possible sweep parameters and their unit
                        parameter: 
                            the QCoDeS parameter to be swept over

                        sweep_list: the sweep list [start, end, step amount] 

                return: True if valid configuration, False if not 
        '''

        #Check wether we can actually loop over each parameter
        if parameter.name not in possible_sweep_params.keys():
            print("Invalid sweep parameter")
            return False

        elif len(sweep_list) != 3:
            print("Invalid sweep list")
            return False 

        #Validate the sweep start and end
        for value in sweep_list[:2]:
            try:
                parameter.validate(value)
            except ValueError:
                print(f"Sweep range for variable {parameter.name} is outside of bounds {parameter.vals}.")
                return False

        return True



    def initialize_qick_program(self, sweep_configuration, qicksoc, config, protocol):
        '''
        This function handles the proper initialization of 
        the program config and protocol.

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
                  "sweep_variables": sweep_configuration
              }

        for sweep_variable in sweep_configuration:
            iq_config[sweep_variable] = sweep_configuration[sweep_variable][0]


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
        dimension = 0
        possible_sweep_params = {"pulse_freq":"MHz",
                                 "pulse_gain":"DAC units",
                                 "pulse_phase":"deg",
                                 "pulse_length":"us",
                                 "delay_time": "us"}
        sweep_param_objects = []
        sweep_configuration = {}

        #Input validation
        for parameter in params_and_values:
            if self.validate_sweep(possible_sweep_params, 
                                   parameter,
                                   params_and_values[parameter]):

                sweep_configuration[parameter.name] = params_and_values[parameter]
            else:
                return 

        #Configure the default config
        zcu_config = self.zcu.generate_config()
        # initialize qcodes
        experiment = qc.load_or_create_experiment( 
                experiment_name="zcu_qcodes_test", 
                sample_name=protocol.name)

        meas = qc.Measurement(exp=experiment)

        #Create manual parameters for gathering data
        for sweepable_variable in sweep_configuration:

            #Define the manual parameters
            sweep_param_object = qc.ManualParameter(sweepable_variable, 
                    instrument = None,
                    unit=possible_sweep_params[sweepable_variable],
                    initial_value = sweep_configuration[sweepable_variable][0])

            dimension += 1
            sweep_param_objects.append(sweep_param_object)
            meas.register_parameter(sweep_param_object)
    

        #Define the custom parameters which are dependent on the manual parameters
        sweep_param_objects.reverse()
        meas.register_custom_parameter("avg_i", setpoints=sweep_param_objects)
        meas.register_custom_parameter("avg_q", setpoints=sweep_param_objects)

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

            #Troubleshooting
            #return expt_pts, avg_i, avg_q

            #Divide the expt_pts array into individual measurement points
            #for each sweepable variable.
            sweep_param_objects.reverse()
            for i in range(dimension):
                param_values.append((sweep_param_objects[i], expt_pts[i]))
    
    
            datasaver.add_result( ("avg_i", avg_i), ("avg_q", avg_q), *param_values)

        #Return the run_id
        run_id = datasaver.dataset.captured_run_id
        return run_id



