from typing import Any

from qcodes_qick.channels import DacChannel
from qcodes_qick.instruction_base import QickInstruction
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters import TProcSecParameter
from qcodes_qick.protocol_base import HardwareSweep, SweepProgram
from qick.averager_program import QickSweep


class Delay(QickInstruction):
    def __init__(
        self, parent: QickInstrument, dac: DacChannel, name="Delay", **kwargs: Any
    ):
        super().__init__(parent, name, **kwargs)
        self.dac = dac

        self.time = TProcSecParameter(
            name="time",
            instrument=self,
            label="Delay time",
            initial_value=1e-6,
            qick_instrument=self.parent,
        )

    def initialize(self, program: SweepProgram):
        self.time_reg = program.new_gen_reg(
            gen_ch=self.dac.channel,
            init_val=self.time.get() * 1e6,
            reg_type="time",
            tproc_reg=True,
        )

    def play(self, program: SweepProgram):
        assert self in program.protocol.instructions
        program.sync_all()
        program.sync(self.time_reg.page, self.time_reg.addr)

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        if sweep.parameter is self.time:
            reg = self.time_reg
            program.add_sweep(
                QickSweep(self, reg, sweep.start * 1e6, sweep.stop * 1e6, sweep.num)
            )
        else:
            raise NotImplementedError(f"cannot sweep over {sweep.parameter.name}")
