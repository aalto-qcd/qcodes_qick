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
        self.add_component(ZCU216MetaInstrument(name='zcu', label='ZCU216'))
  
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

    def print_configuration(self):
        print("Station configuration:\n\n")
        for instrument in self.components:
            print("-----" + self.components[instrument].label + "----\n")
            self.components[instrument].print_readable_snapshot()

    def print_io_configuration(self):
        print("Station IO configuration:\n\n")
        for instrument in self.components:
            try:
                if self.components[instrument].isADC or self.components[instrument].isDAC:
                    print("-----" + self.components[instrument].label + "----\n")
                    self.components[instrument].print_readable_snapshot()
            except:
                pass

    def troubleshoot(self):
        return self.zcu.return_soc()

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
                    params_and_values : dict[qc.Parameter, list[float]],
                    protocol : Protocol,
                    dac_channels : dict[str : qc.Instrument],
                    adc_channels: dict[str : qc.Instrument]):
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
        io_data = { **dac_channels, **adc_channels }
        protocol.set_io(io_data)
        protocol.validate_params(params_and_values)

        #After input validation, we want to 
        #Configure the default config that will remain constant through the measurement

        dimension = 0
        sweep_param_objects = []
        sweep_configuration = {}

        # initialize qcodes
        # this will be removed in the final product (the user initializes their own experiment)

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


