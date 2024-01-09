import qcodes as qc
from qcodes.instrument import Instrument, ManualParameter
from qcodes.station import Station
from qcodes.utils.validators import Numbers, MultiType, Ints
from qick import *
from qick.averager_program import QickSweep
from measurements.Protocols import Protocol
from metainstruments.ZCUMetainstrument import ZCU216Metainstrument
from metainstruments.QICKChannel import DACChannel, ADCChannel
from typing import List, Dict
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
        self.add_component(ZCU216Metainstrument(name='zcu'))

  
    def add_DAC_channel(self, channel: int, name: str):
        if channel in self.zcu.validDACs:
            try:
                self.add_component(DACChannel(name = name, channel_number = channel))
            except:
                pass
        else:
            raise Exception("Invalid DAC channel number")


    def add_ADC_channel(self, channel: int, name: str):
        if channel in self.zcu.validADCs:
            try:
                self.add_component(ADCChannel(name = name, channel_number = channel))
            except:
                pass
        else:
            raise Exception("Invalid ADC channel number")

    def add_protocol(self, protocol: Protocol):
        try:
            self.add_component(protocol)
        except:
            pass

    def print_configuration(self):
        print("Station configuration:\n\n")
        for instrument in self.components:
            self.components[instrument].print_readable_snapshot()
            print()

    def print_io_configuration(self):
        print("Station IO configuration:\n\n")
        for instrument in self.components:
            try:
                if self.components[instrument].isADC or self.components[instrument].isDAC:
                    self.components[instrument].print_readable_snapshot()
                    print()
            except:
                pass

    def troubleshoot(self):
        return self.zcu.return_soc()

    def remove_protocol(self, protocol: Protocol):
        try:
            self.remove_component(protocol.name)
        except:
            pass

    def measure_iq( self,  
                    params_and_values : Dict[qc.Parameter, List[float]],
                    protocol : Protocol,
                    dac_channels : Dict[str, qc.Instrument],
                    adc_channels: Dict[str, qc.Instrument]):
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

        if protocol not in self.components.values() :
            raise Exception("Protocol not defined as an instrument")
        
        #Here we want to validate the given data, which is protocol dependent.
        io_data = { **dac_channels, **adc_channels }
        protocol.set_io(io_data)
        protocol.validate_params(params_and_values)

        #After input validation, we want to 
        #Configure the default config that will remain constant through the measurement

        sweep_param_objects = []
        sweep_configuration = {}

        # initialize qcodes
        # this will be removed in the final product (the user initializes their own experiment)

        experiment = qc.load_or_create_experiment(
                experiment_name="zcu_qcodes_test",
                sample_name="Herja")

        meas = qc.Measurement(exp=experiment)

        #Create manual parameters for gathering data
        for parameter, values in params_and_values.items():
            sweep_param_objects.append(parameter)
            meas.register_parameter(parameter)


        #Define the custom parameters which are dependent on the manual parameters
        sweep_param_objects.reverse()
        meas.register_custom_parameter("avg_i", setpoints=sweep_param_objects)
        meas.register_custom_parameter("avg_q", setpoints=sweep_param_objects)

        result_param_values = []

        #The qcodes experiment, surrounding the qick program is contained here.
        with meas.run() as datasaver:

            #Initialize the
            program_base_config = protocol.initialize_qick_program(self.zcu.soc, params_and_values)

            #Run the qick program, as defined by the protocol and params_and_values
            expt_pts, avg_i, avg_q = protocol.run_program(program_base_config)

            #Divide the expt_pts array into individual measurement points
            #for each sweepable variable.
            sweep_param_objects.reverse()
            for i in range(len(sweep_param_objects)):
                result_param_values.append((sweep_param_objects[i], expt_pts[i]))

            datasaver.add_result( ("avg_i", avg_i), ("avg_q", avg_q), *result_param_values)

        #Return the run_id
        run_id = datasaver.dataset.captured_run_id

        #This might be unnecessary/annoying. 
        #self.remove_protocol(protocol)

        return run_id


