from typing import Any

from qcodes_qick.channels import DacChannel
from qcodes_qick.instruction_base import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters import DegParameter
from qcodes_qick.protocol_base import HardwareSweep, SweepProgram
from qick.averager_program import QickSweep


class SetPhase(QickInstruction):
    def __init__(
        self, parent: QickInstrument, dac: DacChannel, name="SetPhase", **kwargs: Any
    ):
        super().__init__(parent, name, **kwargs)
        self.dacs = [dac]

        self.phase = DegParameter(
            name="phase",
            instrument=self,
            label="phase",
            initial_value=0,
            channel=self.dacs[0],
        )

    def initialize(self, program: SweepProgram):
        self.dac_phase_reg = program.get_gen_reg(self.dacs[0].channel_num, "phase")
        self.phase_reg = program.new_gen_reg(
            gen_ch=self.dacs[0].channel_num,
            init_val=self.phase.get(),
            reg_type="phase",
        )

    def play(self, program: SweepProgram):
        assert self in program.protocol.instructions
        self.dac_phase_reg.set_to(self.phase_reg)

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        if sweep.parameter is self.phase:
            reg = self.phase_reg
            program.add_sweep(
                QickSweep(program, reg, sweep.start_int, sweep.stop_int, sweep.num)
            )
        else:
            raise NotImplementedError(f"cannot sweep over {sweep.parameter.name}")
