import qcodes as qc
from qick import *
from qick.averager_program import QickSweep
from multi_variable_sweep import HardwareSweepProgram, LoopbackProgram
import numpy as np
import itertools

class Protocol:
    def __init__(self):
        pass
            
    def initialize_program(self):
        """ can be used for input validation? """
        pass

    def run_program(self):
        """ handle running the program and aqcuiring the data """
        pass

    def handle_output(self):
        """ output handling? """
        pass



class NDSweepProtocol(Protocol):

    def __init__(self):
        super().__init__()

    def initialize_program(self, soccfg, cfg):
        """ can be used for input validation? """
        self.cfg = cfg
        self.soccfg = soccfg

    def run_program(self):
        sweep_config = self.cfg["sweep_variables"]
        if "freq" in sweep_config:
            freqs = np.linspace(sweep_config["freq"][0], sweep_config["freq"][1], sweep_config["freq"][2])
            sweep_config.pop("freq")
            q_data = []
            i_data = []
            

            for freq in freqs:
                self.cfg["pulse_freq"] = freq
                prog = HardwareSweepProgram(self.soccfg, self.cfg)
                expt_pts, avg_q, avg_i = prog.acquire(self.soccfg, load_pulses=True)
                q_data.append(avg_q) 
                i_data.append(avg_i) 

            q_data = np.concatenate( q_data, axis=0 )
            i_data = np.concatenate( i_data, axis=0 )
            expt_pts.append(freqs)
            return self.handle_output(expt_pts, q_data, i_data)
                
        
        else:
            prog = HardwareSweepProgram(self.soccfg, self.cfg)
            expt_pts, avg_q, avg_i = prog.acquire(self.soccfg, load_pulses=True)
            expt_pts, avg_q, avg_i = self.handle_output(expt_pts, avg_q, avg_i)
            return expt_pts, avg_q, avg_i 


    def handle_output(self, expt_pts, avg_i, avg_q):
        datapoints = len(avg_i.flatten())
        new_expt_pts = [[] for i in range(len(expt_pts))]

        for point in list(itertools.product( *expt_pts )):
            
            coord_index = 0
            for coordinate in point:
                new_expt_pts[coord_index].append(coordinate)
                coord_index += 1


        return new_expt_pts, avg_q, avg_i 

