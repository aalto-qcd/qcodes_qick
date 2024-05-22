from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from qcodes.instrument import InstrumentModule

if TYPE_CHECKING:
    from qcodes_qick.channels import AdcChannel, DacChannel
    from qcodes_qick.instruments import QickInstrument
    from qcodes_qick.protocol_base import HardwareSweep, SweepProgram


class QickInstruction(InstrumentModule):
    parent: QickInstrument

    def __init__(self, parent: QickInstrument, name: str, **kwargs: Any):
        super().__init__(parent, name, **kwargs)
        self.dac: Optional[DacChannel] = None
        self.adc: Optional[AdcChannel] = None
        parent.add_submodule(name, self)

    def initialize(self, program: SweepProgram):
        pass

    def play(self, program: SweepProgram):
        pass

    def add_sweep(self, program: SweepProgram, sweep: HardwareSweep):
        raise NotImplementedError(f"cannot sweep over {sweep.parameter.name}")
