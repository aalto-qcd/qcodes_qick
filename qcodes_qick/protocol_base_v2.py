from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence

import numpy as np
from qcodes import ManualParameter, Measurement, Parameter
from qcodes.instrument import InstrumentModule
from qcodes.validators import Ints
from qick.asm_v2 import AveragerProgramV2, QickSweep
from qick.qick_asm import AcquireMixin
from tqdm.contrib.itertools import product as tqdm_product

from qcodes_qick.parameters_v2 import SweepableNumbers, SweepableParameter

if TYPE_CHECKING:
    from qcodes.dataset.measurements import DataSaver
    from qick.qick_asm import QickConfig

    from qcodes_qick.channels_v2 import AdcChannel, DacChannel
    from qcodes_qick.envelope_base_v2 import DacEnvelope
    from qcodes_qick.instruction_base_v2 import QickInstruction
    from qcodes_qick.instruments import QickInstrument


class QickProtocol(InstrumentModule):
    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.instructions: Sequence[QickInstruction] = []
        assert parent.tproc_version.get() == 2
        parent.add_submodule(name, self)


class SoftwareSweep:
    parameters: Sequence[Parameter]
    values: Sequence[float]

    def __init__(
        self,
        parameters: Parameter | Sequence[Parameter],
        start: float | Sequence[float],
        stop: float | None = None,
        num: int | None = None,
        skip_first: bool = False,
        skip_last: bool = False,
    ):
        if isinstance(parameters, Parameter):
            self.parameters = [parameters]
        else:
            self.parameters = parameters

        # make sure that all parameters have the same unit
        assert len({parameter.unit for parameter in self.parameters}) == 1

        if isinstance(start, Sequence):
            self.values = start
        else:
            self.values = np.linspace(start, stop, num)
        if skip_first:
            self.values = self.values[1:]
        if skip_last:
            self.values = self.values[:-1]


class SweepProtocol(ABC, QickProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        name: str,
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)

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
        self.final_delay = SweepableParameter(
            name="final_delay",
            instrument=self,
            label="Delay time to add at the end of the shot timeline, after the end of the last pulse or readout",
            unit="sec",
            vals=SweepableNumbers(min_value=0),
            initial_value=1e-6,
        )
        self.final_wait = SweepableParameter(
            name="final_wait",
            instrument=self,
            label="Amount of time to pause tProc execution at the end of each shot, after the end of the last readout",
            unit="sec",
            vals=SweepableNumbers(min_value=0),
            initial_value=0,
        )
        self.initial_delay = SweepableParameter(
            name="initial_delay",
            instrument=self,
            label="Delay time to add to the timeline before starting to run the loops, to allow enough time for tProc to execute your initialization commands",
            unit="sec",
            vals=SweepableNumbers(min_value=0),
            initial_value=1e-6,
        )

    @abstractmethod
    def generate_program(
        self, soccfg: QickConfig, hardware_loop_counts: dict[str, int]
    ) -> SweepProgram: ...

    def run(
        self,
        meas: Measurement,
        software_sweeps: Sequence[SoftwareSweep] = (),
        hardware_loop_counts: dict[str, int] | None = None,
        decimated: bool = False,
    ) -> int:
        hardware_loop_counts = hardware_loop_counts if hardware_loop_counts else {}

        # initialize and register the software sweep parameters
        software_sweep_parameters = []
        for sweep in software_sweeps:
            sweep.parameters[0].set(sweep.values[0])
            software_sweep_parameters.append(sweep.parameters[0])
            meas.register_parameter(sweep.parameters[0], paramtype="array")
            for parameter in sweep.parameters[1:]:
                parameter.set(sweep.values[0])

        # register the hardware sweep parameters
        hardware_sweep_parameters = []
        for loop in hardware_loop_counts:
            for parameter in self.parent.swept_parameters:
                sweep = parameter.get()
                assert isinstance(sweep, QickSweep)
                if loop in sweep.spans and parameter not in hardware_sweep_parameters:
                    hardware_sweep_parameters.append(parameter)
                    meas.register_parameter(parameter, paramtype="array")

        # register the time axis if necessary
        time_parameters = []
        if decimated:
            time_parameter = Parameter("time", label="Time", unit="sec")
            time_parameters.append(time_parameter)
            meas.register_parameter(time_parameter, paramtype="array")

        # generate the program just to obtain the ADC channel numbers and the number of readouts per shot
        program = self.generate_program(self.parent.soccfg, hardware_loop_counts)
        adc_channel_nums = program.ro_chs.keys()
        reads_per_shot = program.reads_per_shot
        assert len(adc_channel_nums) == len(reads_per_shot)
        assert sum(reads_per_shot) > 0

        # create and register the parameters representing the acquired data
        setpoints = (
            hardware_sweep_parameters + software_sweep_parameters + time_parameters
        )
        iq_parameters = []
        for i, channel_num in enumerate(adc_channel_nums):
            for readout_num in range(reads_per_shot[i]):
                name = "iq"
                if reads_per_shot[i] > 1:
                    name += f"{readout_num}"
                if len(adc_channel_nums) > 1:
                    name += f"_ch{channel_num}"

                iq_parameter = Parameter(name)
                iq_parameters.append(iq_parameter)
                meas.register_parameter(iq_parameter, setpoints, paramtype="array")

        with meas.run() as datasaver:
            if len(software_sweeps) == 0:
                if decimated:
                    self.run_hardware_loops_decimated(
                        datasaver,
                        software_sweeps,
                        hardware_loop_counts,
                        hardware_sweep_parameters,
                        time_parameter,
                        iq_parameters,
                        progress=True,
                    )
                else:
                    self.run_hardware_loops(
                        datasaver,
                        software_sweeps,
                        hardware_loop_counts,
                        hardware_sweep_parameters,
                        iq_parameters,
                        progress=True,
                    )
            else:
                software_sweep_values = [sweep.values for sweep in software_sweeps]
                for current_values in tqdm_product(*software_sweep_values):
                    for sweep, value in zip(software_sweeps, current_values):
                        for parameter in sweep.parameters:
                            parameter.set(value)
                    if decimated:
                        self.run_hardware_loops_decimated(
                            datasaver,
                            software_sweeps,
                            hardware_loop_counts,
                            hardware_sweep_parameters,
                            time_parameter,
                            iq_parameters,
                            progress=False,
                        )
                    else:
                        self.run_hardware_loops(
                            datasaver,
                            software_sweeps,
                            hardware_loop_counts,
                            hardware_sweep_parameters,
                            iq_parameters,
                            progress=False,
                        )

        return datasaver.run_id

    def run_hardware_loops(
        self,
        datasaver: DataSaver,
        software_sweeps: Sequence[SoftwareSweep],
        hardware_loop_counts: dict[str, int],
        hardware_sweep_parameters: Sequence[SweepableParameter],
        iq_parameters: Sequence[Parameter],
        progress: bool = True,
    ):
        # Run the program
        program = self.generate_program(self.parent.soccfg, hardware_loop_counts)
        all_iq = AcquireMixin.acquire(
            self=program,
            soc=self.parent.soc,
            soft_avgs=self.soft_avgs.get(),
            progress=progress,
        )

        reads_per_shot = program.reads_per_shot
        iq_index = 0
        for channel_index in range(len(reads_per_shot)):
            channel_iq = all_iq[channel_index]
            channel_iq = channel_iq.reshape(reads_per_shot[channel_index], -1, 2)
            for readout_num in range(reads_per_shot[channel_index]):
                iq = channel_iq[readout_num, :, :].dot([1, 1j])
                result = []

                # Add software sweep paramters to the result
                for sweep in software_sweeps:
                    result.append((sweep.parameters[0], sweep.parameters[0].get()))

                # Add hardware sweep parameters to the result
                for parameter in hardware_sweep_parameters:
                    sweep = parameter.get()
                    assert isinstance(sweep, QickSweep)
                    coordinates = sweep.get_actual_values(hardware_loop_counts)
                    result.append((parameter, coordinates))

                # Add acquired data to the result
                result.append((iq_parameters[iq_index], iq))
                iq_index += 1

                datasaver.add_result(*result)

    def run_hardware_loops_decimated(
        self,
        datasaver: DataSaver,
        software_sweeps: Sequence[SoftwareSweep],
        hardware_loop_counts: dict[str, int],
        hardware_sweep_parameters: Sequence[SweepableParameter],
        time_parameter: Parameter,
        iq_parameters: Sequence[Parameter],
        progress: bool = True,
    ):
        # Run the program
        program = self.generate_program(self.parent.soccfg, hardware_loop_counts)
        all_iq = AcquireMixin.acquire_decimated(
            self=program,
            soc=self.parent.soc,
            soft_avgs=self.soft_avgs.get(),
            progress=progress,
        )

        reads_per_shot = program.reads_per_shot
        iq_index = 0
        for channel_index in range(len(reads_per_shot)):
            channel_iq = all_iq[channel_index]
            length = len(program.get_time_axis(channel_index))
            channel_iq = channel_iq.reshape(
                self.hard_avgs.get(), -1, reads_per_shot[channel_index], length, 2
            )
            for readout_num in range(reads_per_shot[channel_index]):
                iq = channel_iq[:, :, readout_num, :, :].mean(axis=0).dot([1, 1j])
                result = []

                # Add software sweep paramters to the result
                for sweep in software_sweeps:
                    result.append((sweep.parameters[0], sweep.parameters[0].get()))

                # Add hardware sweep parameters to the result
                for parameter in hardware_sweep_parameters:
                    sweep = parameter.get()
                    assert isinstance(sweep, QickSweep)
                    coordinates = sweep.get_actual_values(hardware_loop_counts)
                    result.append((parameter, coordinates[..., np.newaxis]))

                time = program.get_time_axis(channel_index) / 1e6
                result.append((time_parameter, time))

                # Add acquired data to the result
                result.append((iq_parameters[iq_index], iq.reshape(-1)))
                iq_index += 1

                datasaver.add_result(*result)


class SweepProgram(AveragerProgramV2):
    def __init__(
        self,
        soccfg: QickConfig,
        protocol: SweepProtocol,
        hardware_loop_counts: dict[str, int],
    ):
        self.protocol = protocol
        self.hardware_loop_counts = hardware_loop_counts
        self.dacs: set[DacChannel] = set().union(
            *(instruction.dacs for instruction in self.protocol.instructions)
        )
        self.adcs: set[AdcChannel] = set().union(
            *(instruction.adcs for instruction in self.protocol.instructions)
        )
        self.dac_envelopes: set[DacEnvelope] = set().union(
            *(instruction.dac_envelopes for instruction in self.protocol.instructions)
        )
        super().__init__(
            soccfg,
            reps=protocol.hard_avgs.get(),
            final_delay=protocol.final_delay.get() * 1e6,
            final_wait=protocol.final_wait.get() * 1e6,
            initial_delay=protocol.initial_delay.get() * 1e6,
        )

    def _initialize(self, cfg: dict):  # noqa: ARG002
        for dac in self.dacs:
            dac.initialize(self)
        for adc in self.adcs:
            adc.initialize(self)
        for envelope in self.dac_envelopes:
            envelope.initialize(self)
        for instruction in set(self.protocol.instructions):
            instruction.initialize(self)
        for name, count in self.hardware_loop_counts.items():
            self.add_loop(name, count)


class SimpleSweepProtocol(SweepProtocol):
    def __init__(
        self,
        parent: QickInstrument,
        instructions: Sequence[QickInstruction],
        name="SimpleSweepProtocol",
        **kwargs,
    ):
        super().__init__(parent, name, **kwargs)
        self.instructions = instructions

    def generate_program(
        self, soccfg: QickConfig, hardware_loop_counts: dict[str, int]
    ):
        return SimpleSweepProgram(soccfg, self, hardware_loop_counts)


class SimpleSweepProgram(SweepProgram):
    protocol: SimpleSweepProtocol

    def _body(self, cfg: dict):  # noqa: ARG002
        for instruction in self.protocol.instructions:
            instruction.append_to(self)
