from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qcodes.instrument import InstrumentModule

if TYPE_CHECKING:
    from qcodes_qick.channels import AdcChannel, DacChannel
    from qcodes_qick.instruments import QickInstrument
    from qcodes_qick.protocol_base import HardwareSweep, SweepProgram
    from qick.asm_v1 import QickProgram


class QickPulse(InstrumentModule):

    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, **kwargs: Any):
        super().__init__(parent, name, **kwargs)
        self.dacs: set[DacChannel] = {}
        self.adcs: set[AdcChannel] = {}
        parent.add_submodule(name, self)

    def initialize(self, program: QickProgram):
        pass

    def play(self, program: QickProgram):
        pass

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        raise NotImplementedError
