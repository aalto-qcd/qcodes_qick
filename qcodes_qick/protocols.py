import itertools
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from qcodes import Instrument, Parameter
from tqdm.auto import tqdm

from qcodes_qick.parameters import QuantizedParameter
from qick import QickConfig


@dataclass
class SoftwareSweep:
    parameter: Parameter
    values: Sequence


class HardwareSweep:
    def __init__(
        self, parameter: QuantizedParameter, start: float, step: float, num: int
    ):
        self.parameter = parameter
        self.start_int = parameter.float2int(start)
        self.start = parameter.int2float(self.start_int)
        self.step_int = parameter.float2int(step)
        self.step = parameter.int2float(self.step_int)
        self.num = num
        self.values = self.start + self.step * np.arange(num)


class Protocol(Instrument):

    def run_hybrid_loop_program(self, soc, cfg, program):
        # ONLY FOR RAVERAGERPROGRAMS

        soccfg = QickConfig(soc.get_cfg())
        software_iterators = {}
        iterations = 1

        for parameter_name, value in cfg.items():
            if type(value) == list:
                software_iterators[parameter_name] = np.linspace(
                    value[0], value[1], value[2]
                ).tolist()
                iterations = iterations * value[2]

        if len(software_iterators) == 0:
            prog = program(soccfg, cfg)
            expt_pts, avg_i, avg_q = prog.acquire(soc, load_pulses=True, progress=True)
            expt_pts, avg_i, avg_q = self.handle_hybrid_loop_output(
                [expt_pts], avg_i, avg_q
            )
            avg_i = np.squeeze(avg_i.flatten())
            avg_q = np.squeeze(avg_q.flatten())

            return expt_pts, avg_i, avg_q

        else:

            iteratorlist = list(software_iterators)
            software_expt_data = [[] for i in range(len(software_iterators))]
            hardware_expt_data = []
            i_data = []
            q_data = []

            for coordinate_point in tqdm(
                itertools.product(*list(software_iterators.values())), total=iterations
            ):

                for coordinate_index in range(len(coordinate_point)):
                    cfg[iteratorlist[coordinate_index]] = coordinate_point[
                        coordinate_index
                    ]

                prog = program(soccfg, cfg)
                expt_pts, avg_i, avg_q = prog.acquire(soc, load_pulses=True)

                # Problems arise here with NDAveragerprograms :)
                expt_pts, avg_i, avg_q = self.handle_hybrid_loop_output(
                    [expt_pts], avg_i, avg_q
                )
                i_data.extend([avg_i[0][i] for i in range(len(avg_i[0]))])
                q_data.extend([avg_q[0][i] for i in range(len(avg_q[0]))])

                for i in range(len(software_iterators)):
                    software_expt_data[i].extend(
                        [coordinate_point[i] for k in range(len(expt_pts[0]))]
                    )

                hardware_expt_data.extend(
                    [expt_pts[0][i] for i in range(len(expt_pts[0]))]
                )

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
        # New version of qick returns lists containing np arrays,
        # formerly only np arrays :)
        avg_i = avg_i[0]
        avg_q = avg_q[0]
        datapoints = len(avg_i.flatten())
        new_expt_pts = [[] for i in range(len(expt_pts))]

        for point in list(itertools.product(*expt_pts)):

            coord_index = 0
            for coordinate in point:
                new_expt_pts[coord_index].append(coordinate)
                coord_index += 1

        return new_expt_pts, avg_i, avg_q
