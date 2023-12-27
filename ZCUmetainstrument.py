import qcodes as qc
from qcodes.instrument import Instrument, ManualParameter
from qcodes.station import Station
from qcodes.utils.validators import Numbers, MultiType, Ints 
from qick import *
from ZCUprotocols import Protocol, NDSweepProtocol 
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
        parameters are defined and initialized. All parameters receive some
        initial value, but those that initial values corresponding to variables
        that are sweeped over are overwritten.
        '''

        super().__init__(name, **kwargs)

        self.soc = QickSoc()

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
                            vals = Numbers(*[0,150]),
                            unit = 'us',
                            initial_value = 0.1)

        self.add_parameter('adc_trig_offset',
                            parameter_class=ManualParameter,
                            label='ADC trigger offset',
                            vals = Numbers(*[0,150]),
                            unit = 'us',
                            initial_value = 1)

        self.add_parameter('soft_avgs',
                            parameter_class=ManualParameter,
                            label='Soft averages',
                            vals = Ints(*[0,5000]),
                            initial_value = 1)

        self.add_parameter('qubit_ch',
                            parameter_class=ManualParameter,
                            label='Qubit probe channel',
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

