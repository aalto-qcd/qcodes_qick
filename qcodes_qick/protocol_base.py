from __future__ import annotations

import itertools
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Union

import numpy as np
from qcodes import ManualParameter, Measurement, Parameter, Station
from qcodes.dataset.experiment_container import Experiment
from qcodes.instrument import InstrumentModule
from qcodes.validators import Ints
from tqdm.contrib.itertools import product as tqdm_product

from qcodes_qick.parameters import HardwareParameter
from qick.asm_v1 import QickProgram
from qick.averager_program import NDAveragerProgram

if TYPE_CHECKING:
    from qcodes_qick.instruments import QickInstrument


class QickProtocol(InstrumentModule):

    parent: QickInstrument

    def __init__(
        self,
        station: Station,
        parent: QickInstrument,
        name: str,
        program_class: type[QickProgram],
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.station = station
        self.program_class = program_class
        parent.add_submodule(name, self)


class SoftwareSweep:

    values: Sequence[float]

    def __init__(
        self,
        parameter: Parameter,
        start: Union[float, Sequence[float]],
        stop: Optional[float] = None,
        num: Optional[int] = None,
        skip_first: bool = False,
        skip_last: bool = False,
    ):
        self.parameter = parameter

        if isinstance(start, Sequence):
            self.values = start
        else:
            self.values = np.linspace(start, stop, num)
        if skip_first:
            self.values = self.values[1:]
        if skip_last:
            self.values = self.values[:-1]


class HardwareSweep:
    def __init__(
        self,
        parameter: HardwareParameter,
        start: float,
        stop: float,
        num: int,
        skip_first: bool = False,
        skip_last: bool = False,
    ):
        self.parameter = parameter

        self.step_int = parameter.float2int((stop - start) / (num - 1))
        self.values_int = parameter.float2int(start) + self.step_int * np.arange(num, dtype=np.int64)
        if skip_first:
            self.values_int = self.values_int[1:]
        if skip_last: 
            self.values_int = self.values_int[:-1]
        self.start_int = self.values_int[0]
        self.stop_int = self.values_int[-1]
        self.num = len(self.values_int)

        self.start = parameter.int2float(self.start_int)
        self.stop = parameter.int2float(self.stop_int)
        self.step = parameter.int2float(self.step_int)
        self.values = np.array([parameter.int2float(i) for i in self.values_int])


class NDAveragerProtocol(QickProtocol):

    program_class: type[NDAveragerProgram]

    def __init__(
        self,
        station: Station,
        parent: QickInstrument,
        name: str,
        program_class: type[NDAveragerProgram],
        **kwargs,
    ):
        super().__init__(station, parent, name, program_class, **kwargs)

        self.hard_avgs = ManualParameter(
            name="hard_avgs",
            instrument=self,
            label="Number of hardware repetitions to average over",
            vals=Ints(min_value=0),
            initial_value=1000,
        )

        self.soft_avgs = ManualParameter(
            name="soft_avgs",
            instrument=self,
            label="Number of software repetitions to average over",
            vals=Ints(min_value=0),
            initial_value=1,
        )

    def run(
        self,
        experiment: Experiment,
        software_sweeps: Sequence[SoftwareSweep] = (),
        hardware_sweeps: Sequence[HardwareSweep] = (),
    ) -> int:

        # instantiate the program just to obtain the ADC channel numbers and the number of readouts per experiment
        cfg = {"reps": 1, "protocol": self}
        program = self.program_class(self.parent.soccfg, cfg)
        adc_channels = program.ro_chs.keys()
        readouts_per_experiment = program.reads_per_shot
        assert len(adc_channels) == len(readouts_per_experiment)

        # set sweep parameters to start values
        for sweep in itertools.chain(software_sweeps, hardware_sweeps):
            sweep.parameter.set(sweep.values[0])

        meas = Measurement(experiment, self.station, self.name)
        setpoints = []

        # register the sweep parameters
        for sweep in itertools.chain(software_sweeps, hardware_sweeps):
            setpoints.append(sweep.parameter)
            meas.register_parameter(sweep.parameter, paramtype="array")

        # create and register the parameters representing the acquired data
        iq_parameters = []
        for i, channel in enumerate(adc_channels):
            for readout_number in range(readouts_per_experiment[i]):
                name = "iq"
                if readouts_per_experiment[i] > 1:
                    name += f"{readout_number}"
                if len(adc_channels) > 1:
                    name += f"_ch{channel}"
                iq_parameters.append(Parameter(name))
                meas.register_parameter(
                    iq_parameters[channel], setpoints=setpoints, paramtype="array"
                )

        with meas.run() as datasaver:
            soft_parameters = [sweep.parameter for sweep in software_sweeps]
            hard_parameters = [sweep.parameter for sweep in hardware_sweeps]

            if len(software_sweeps) == 0:
                hard_coordinates, iq = self.run_hardware_sweeps(
                    hardware_sweeps, progress=True
                )

                result = []
                for parameter, value in zip(hard_parameters, hard_coordinates):
                    result.append((parameter, value))
                for parameter, value in zip(iq_parameters, iq):
                    result.append((parameter, value))
                datasaver.add_result(*result)

            else:
                soft_sweep_values = [sweep.values for sweep in software_sweeps]

                for current_values in tqdm_product(*soft_sweep_values):

                    # set software sweep parameters to current values
                    for parameter, value in zip(soft_parameters, current_values):
                        parameter.set(value)

                    hard_coordinates, iq = self.run_hardware_sweeps(
                        hardware_sweeps, progress=False
                    )

                    result = []
                    for parameter, value in zip(soft_parameters, current_values):
                        result.append((parameter, value))
                    for parameter, value in zip(hard_parameters, hard_coordinates):
                        result.append((parameter, value))
                    for parameter, value in zip(iq_parameters, iq):
                        result.append((parameter, value))
                    datasaver.add_result(*result)

        return datasaver.run_id

    def run_hardware_sweeps(
        self,
        hardware_sweeps: Sequence[HardwareSweep],
        progress: bool = True,
    ):

        cfg = {
            "reps": self.hard_avgs.get(),
            "soft_avgs": self.soft_avgs.get(),
            "hardware_sweeps": hardware_sweeps,
            "protocol": self,
        }
        program = self.program_class(self.parent.soccfg, cfg)
        _, avg_di, avg_dq = program.acquire(
            self.parent.soc, load_pulses=True, progress=progress
        )

        # Make a list[np.ndarray] of all the coordinate points of the N-dimensional sweep.
        # sweep_coordinates[n] contains the value of hardware_sweeps[n].parameter used in each experiment.
        # sweep_coordinates[n].shape = (sweep.num for sweep in hardware_sweeps)
        sweep_values = [sweep.values for sweep in hardware_sweeps]
        sweep_coordinates = np.meshgrid(*sweep_values, indexing="ij")

        iq = np.concatenate([i + 1j * q for i, q in zip(avg_di, avg_dq)])
        return sweep_coordinates, iq
