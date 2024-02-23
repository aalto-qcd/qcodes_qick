import qcodes as qc
from qcodes.instrument import InstrumentBase, ManualParameter
from qcodes.station import Station
from qcodes.utils.validators import Numbers, MultiType, Ints 
from qick import *
from qick import QickConfig
import Pyro4


import numpy as np


class QickInstrument(InstrumentBase):
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

        #Pyro4 Socket initialization


        Pyro4.config.SERIALIZER = "pickle"
        Pyro4.config.PICKLE_PROTOCOL_VERSION=4
        

        #IP ADDRESS AND PORT OF THE NAMESERVER
        ns_host = "10.0.100.16"
        ns_port = 8888
        proxy_name = "myqick"
        
        ns = Pyro4.locateNS(host=ns_host, port=ns_port)

        # print the nameserver entries: you should see the QickSoc proxy
        for k,v in ns.list().items():
            print(k,v)

        self.soc = Pyro4.Proxy(ns.lookup(proxy_name))

        self.validADCs = [0,1]
        self.validDACs = [0,1,2,3,4,5,6]

    def ask(self, cmd):
        pass

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

    def get_soccfg(self):
        """
        In this function, we generate a qick configuration dictionary based
        on the parameters in the metainstrument, which the user may have set
        before running a measurement.

        return: qick configuration dict
        """

                
        return QickConfig(self.soc.get_cfg())



