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

    def __init__(self, **kwargs):
        '''
        As we initialize the metainstrument, each of the gettable and settable 
        parameters are defined and initialized. All parameters receive some
        initial value, but those that initial values corresponding to variables
        that are sweeped over are overwritten.
        '''

        super().__init__(**kwargs)

        self.soc = QickSoc()

        self.validADCs = [0,1]
        self.validDACs = [0,1,2,3,4,5,6]



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

    def return_soc(self):
        """
        In this function, we generate a qick configuration dictionary based
        on the parameters in the metainstrument, which the user may have set
        before running a measurement.

        return: qick configuration dict
        """

                
        return self.soc



