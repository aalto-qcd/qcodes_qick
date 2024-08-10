from qcodes import ManualParameter
from qcodes.validators import Numbers

from qcodes_qick.channels_v2 import DacChannel
from qcodes_qick.envelope_base_v2 import DacEnvelope
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.protocol_base import SweepProgram


class GaussianDragEnvelope(DacEnvelope):
    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        name="GaussianDragEnvelope",
        **kwargs,
    ):
        super().__init__(parent, dac, name, **kwargs)
        self.sigma = ManualParameter(
            name="sigma",
            instrument=self,
            label="Standard deviation of the gaussian",
            unit="sec",
            vals=Numbers(min_value=0),
            initial_value=100e-9,
        )
        self.length = ManualParameter(
            name="length",
            instrument=self,
            label="Pulse length",
            unit="sec",
            vals=Numbers(min_value=0),
            initial_value=400e-9,
        )
        self.delta = ManualParameter(
            name="delta",
            instrument=self,
            label="Anharmonicity of the qubit",
            unit="Hz",
            vals=Numbers(),
            initial_value=-200e6,
        )
        self.alpha = ManualParameter(
            name="alpha",
            instrument=self,
            label="Alpha parameter of DRAG",
            vals=Numbers(),
            initial_value=0.5,
        )

    def initialize(self, program: SweepProgram):
        program.add_DRAG(
            ch=self.dac.channel_num,
            name=self.name,
            sigma=self.sigma.get() * 1e6,
            length=self.length.get() * 1e6,
            delta=self.delta.get() / 1e6,
            alpha=self.alpha.get(),
        )
