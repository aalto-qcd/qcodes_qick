import qcodes as qc
from qick import *
from qick.averager_program import QickSweep
from measurements.multi_variable_sweep import HardwareSweepProgram, LoopbackProgram
from measurements.pulse_probe_spectroscopy import PulseProbeSpectroscopyProgram
from measurements.t1program import T1Program
import numpy as np
import itertools

class Protocol:
    """
    The protocol class is a wrapper around an actual qick program, which
    handles initializing and running the qick program, and handling output
    into the correct form desired by the ZCUStation. Each protocol corresponds
    to a specific qick program.
    """
    def __init__(self):
        pass
            
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
    def __init__(self):
        """
        Initialize the protocol object.
            
        """
        super().__init__()
        self.name = "T1DecayMeasurement"
        self.measurement_type = "IQ_measurement"

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





class PulseProbeSpectroscopyProtocol(Protocol):
    """
        This protocol initializes and runs a pulse probe spectroscopy
        program, and correctly formats the output into a desired form. 
    """

    def __init__(self):
        """
        Initialize the protocol object.
            
        """
        super().__init__()
        self.name = "PulseProbeSpectroscopyMeasurement"
        self.measurement_type = "IQ_measurement"

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
        #prog = PulseProbeSpectroscopyProgram(self.soccfg, self.cfg)
        #expt_pts, avg_i, avg_q = prog.acquire(self.soccfg, load_pulses=True)
        #Dumb data
        expt_pts = np.array([400, 500])
        avg_i = [np.array([[-0.02673513, -0.02834141]])]
        avg_q = [np.array([[0.08327843, 0.08439062]])]
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


class NDSweepProtocol(Protocol):
    """
        This protocol initializes and runs a simple N-dimensional sweep,
        and correctly formats the output into a desired form. 
    """

    def __init__(self):
        """
        Initialize the protocol object.
            
        """
        super().__init__()
        self.name = "NDSweepMeasurement"
        self.measurement_type = "IQ_measurement"

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
        sweep_config = self.cfg["sweep_variables"]
        if "pulse_freq" in sweep_config:
            freqs = np.linspace(sweep_config["pulse_freq"][0], sweep_config["pulse_freq"][1], sweep_config["pulse_freq"][2])
            sweep_config.pop("pulse_freq")
            q_data = []
            i_data = []
            

            for freq in freqs:
                self.cfg["pulse_freq"] = freq
                prog = HardwareSweepProgram(self.soccfg, self.cfg)
                expt_pts, avg_i, avg_q = prog.acquire(self.soccfg, load_pulses=True)
                q_data.append(avg_q[0])
                i_data.append(avg_i[0])
            
            i_datalist = np.concatenate( i_data, axis=0 )
            q_datalist = np.concatenate( q_data, axis=0 )
            expt_pts.append(freqs)
            expt_pts, i_data, q_data =  self.handle_output(expt_pts, [ i_datalist ], [ q_datalist ])

            if len(sweep_config) == 1:
                i_data = list(itertools.chain(*i_data))
                q_data = list(itertools.chain(*q_data))
            
            return expt_pts, i_data, q_data 
                
        
        else:
            prog = HardwareSweepProgram(self.soccfg, self.cfg)
            expt_pts, avg_i, avg_q = prog.acquire(self.soccfg, load_pulses=True, progress=True)
            expt_pts, avg_i, avg_q = self.handle_output(expt_pts, avg_i, avg_q)

            for i in range(avg_i.ndim-len(sweep_config)):
                avg_i = np.squeeze(avg_i.flatten())
                avg_q = np.squeeze(avg_q.flatten())


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

