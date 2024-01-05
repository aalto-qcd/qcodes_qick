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

    def set_io(self, io_data : dict[str, qc.Instrument]):
        
        for io_port in io_data.keys():
            if io_data[io_port].isDAC and io_port in self.required_DACs:
                self.validated_IO[io_port] = io_data[io_port]

            elif io_data[io_port].isADC and io_port in self.required_ADCs:
                self.validated_IO[io_port] = io_data[io_port]

            else:
                self.validated_IO = {}
                raise Exception("Invalid IO channel: " + io_port)
                return False
        
        for io_port in { **self.required_DACs, **self.required_ADCs}:
            if io_port not in self.validated_IO:
                self.validated_IO = {}
                raise Exception("Invalid IO channel: " + io_port)
                return False
        else:
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
            
    def initialize_program(self):
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
        self.validated_IO = {}

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
                            initial_value = 1)

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
                            initial_value = 0)

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



    def initialize_program(self, soccfg, cfg):
        """ 
        Initialize the qick soc and qick config
        
        """
        self.cfg = cfg
        self.soccfg = soccfg

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


