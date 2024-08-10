from qcodes import ManualParameter
from qcodes.validators import Numbers

from qcodes_qick.channels_v2 import DacChannel
from qcodes_qick.envelope_base_v2 import DacEnvelope
from qcodes_qick.instruments import QickInstrument
from qcodes_qick.protocol_base import SweepProgram


class GaussianEnvelope(DacEnvelope):
    def __init__(
        self,
        parent: QickInstrument,
        dac: DacChannel,
        name="GaussianEnvelope",
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

    def initialize(self, program: SweepProgram):
        program.add_gauss(
            ch=self.dac.channel_num,
            name=self.name,
            sigma=self.sigma.get() * 1e6,
            length=self.length.get() * 1e6,
        )
