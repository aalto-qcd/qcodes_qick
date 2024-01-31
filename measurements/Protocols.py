import qcodes as qc
import numpy as np
import itertools
from qick import *
from qcodes.instrument import InstrumentBase, ManualParameter
from qcodes.utils.validators import Numbers, MultiType, Ints 
from typing import List, Dict, Any 

from tqdm.auto import tqdm

class Protocol(InstrumentBase):
    """
    The protocol class is a wrapper around an actual qick program, which
    handles initializing and running the qick program, and handling output
    into the correct form desired by the ZCUStation. Each protocol corresponds
    to a specific qick program.
    """
    def __init__(self, name):
        super().__init__(name)
        self.required_DACs = {}
        self.required_ADCs = {}
        self.validated_IO = {}

        #This list contains the sweep parameters, and it is to be deleted after every run
        self.sweep_parameter_list = []
        self.cfg = {}


        pass


    def initialize_qick_program(self, soc, soccfg, sweep_configuration):
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

    def compile_hardware_sweep_dict( self, sweep_configuration : Dict[qc.Parameter, List[float]],  external_parameters : Dict[str, qc.Parameter]):
        """
        This can one day be such that you can sweep all 
        hardware sweepable variables through calling this
        """

        pass



    def set_io(self, io_data : Dict[str, qc.Instrument]):

        temp_IO = self.validated_IO.copy()
        
        for io_port in io_data.keys():
            if io_data[io_port].isDAC and io_port in self.required_DACs:
                temp_IO[io_port] = io_data[io_port]

            elif io_data[io_port].isADC and io_port in self.required_ADCs:
                temp_IO[io_port] = io_data[io_port]

            else:
                raise Exception("Invalid IO channel: " + io_port)
                return False
        
        for io_port in self.validated_IO:
            if io_port is None:
                self.validated_IO = {}
                raise Exception("Invalid IO channel: " + io_port)
                return False
        else:
            self.validated_IO = temp_IO
            return True


    def validate_params(self, params_and_values : Dict[qc.Parameter, np.ndarray]):
        #Validate params and values
        #This is only an elementary check. We want to be able to trust
        #That the iteration list corresponding to the parameter is valid
        for parameter, sweep_configuration in params_and_values.items():
            if parameter.validate(sweep_configuration) is None:
                pass
            else:
                raise Exception("Invalid parameter setpoints: " + parameter.name )
                return False
        return True 
            
    def compile_software_sweep_dict( self, sweep_configuration : Dict[qc.Parameter, np.ndarray],  external_parameters : Dict[str, qc.Parameter]):

        external_parameter_config = {}

        for config_key, parameter in external_parameters.items():
            if parameter in sweep_configuration.keys():
                external_parameter_config[config_key] = sweep_configuration[parameter]
                self.add_sweep_parameter(isHardware = False, parameter = parameter)
            else:
                external_parameter_config[config_key] = parameter.get()

        return external_parameter_config
             


    def run_hybrid_loop_program( self, cfg, program  ): 
        #ONLY FOR RAVERAGERPROGRAMS

        software_iterators = {}
        iterations = 1
    
        for parameter_name, value in cfg.items():
            if type(value) == np.ndarray:
                software_iterators[parameter_name] = value.tolist()
                iterations = iterations*len(value)



        if len(software_iterators) == 0:
            prog = program(self.soccfg, cfg)
            expt_pts, avg_i, avg_q = prog.acquire(self.soc, load_pulses=True, progress=True)
            expt_pts, avg_i, avg_q = self.handle_hybrid_loop_output( [ expt_pts ], avg_i, avg_q)
            avg_i = np.squeeze(avg_i.flatten())
            avg_q = np.squeeze(avg_q.flatten())

            return expt_pts, avg_i, avg_q


        else:

            iteratorlist = list(software_iterators)
            software_expt_data = [ [] for i in range(len(software_iterators))]
            hardware_expt_data = [ ]
            i_data = []
            q_data = []

            for coordinate_point in tqdm(itertools.product(*list(software_iterators.values())), total = iterations):


                for coordinate_index in range(len(coordinate_point)):
                    cfg[iteratorlist[coordinate_index]] = coordinate_point[coordinate_index]


                prog = program(self.soccfg, cfg) 
                expt_pts, avg_i, avg_q = prog.acquire(self.soc, load_pulses=True)

                #Problems arise here with NDAveragerprograms :)
                expt_pts, avg_i, avg_q = self.handle_hybrid_loop_output( [ expt_pts ], avg_i, avg_q )
                i_data.extend([avg_i[0][i] for i in range(len(avg_i[0]))])
                q_data.extend([avg_q[0][i] for i in range(len(avg_q[0]))])
            

                for i in range(len(software_iterators)):
                    software_expt_data[i].extend([ coordinate_point[i] for k in range(len(expt_pts[0]))])

                hardware_expt_data.extend([expt_pts[0][i] for i in range(len(expt_pts[0]))])
                


        software_expt_data.reverse()
        software_expt_data.append(hardware_expt_data)            


        return software_expt_data, i_data, q_data 

    def handle_hybrid_loop_output(self, expt_pts, avg_i, avg_q):
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
        #New version of qick returns lists containing np arrays,
        #formerly only np arrays :)
        avg_i = avg_i[0]
        avg_q = avg_q[0]
        datapoints = len(avg_i.flatten())
        new_expt_pts = [[] for i in range(len(expt_pts))]

        for point in list(itertools.product( *expt_pts )):

            coord_index = 0
            for coordinate in point:
                new_expt_pts[coord_index].append(coordinate)
                coord_index += 1

        return new_expt_pts, avg_i, avg_q

    def add_sweep_parameter(self, isHardware: bool, parameter: qc.Parameter):
        """
        This function adds a sweep parameter in the correct order to the sweep_parameters.
        """
        if isHardware:
            self.sweep_parameter_list.append(parameter)
        else:
            self.sweep_parameter_list.insert(0, parameter)

    def reset_program(self):
        """
        reset the protocol, remove all program specific data, but do not change the internal 
        parameter values
        """
        self.sweep_parameter_list = []
        self.cfg = {}

        























































