import qcodes as qc
from qcodes.instrument import InstrumentBase, ManualParameter
from qcodes.station import Station
from qcodes.utils.validators import Numbers, MultiType, Ints
from qick import *
from qick.averager_program import QickSweep
from measurements.Protocols import Protocol, T1Protocol
from metainstruments.ZCUMetainstrument import ZCU216MetaInstrument
from metainstruments.QICKChannel import DACChannel, ADCChannel
import numpy as np


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
  
    def add_DAC_channel(self, channel: int, name: str):
        if channel in self.zcu.validDACs:
            self.add_component(DACChannel(name = name, channel_number = channel))
        else:
            raise Exception("Invalid DAC channel number")


    def add_ADC_channel(self, channel: int, name: str):
        if channel in self.zcu.validADCs:
            self.add_component(ADCChannel(name = name, channel_number = channel))
        else:
            raise Exception("Invalid ADC channel number")

    def add_protocol(self, protocol: Protocol):
        self.add_component(protocol)

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


    def measure_iq( self,  
                    params_and_values : dict[qc.Parameter, list],
                    protocol : Protocol,
                    dac_channels : dict[str : qc.Instrument],
                    adc_channel: qc.Instrument):
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

        
        #Here we want to validate the given data, which is protocol dependent.

        dimension = 0

        sweep_param_objects = []
        sweep_configuration = {}

        #After input validation, we want to 
        #Configure the default config that will remain constant through the measurement

        zcu_config = self.zcu.generate_config()
        # initialize qcodes

        experiment = qc.load_or_create_experiment(
                experiment_name="zcu_qcodes_test",
                sample_name="Herja")

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


