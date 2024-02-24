from qcodes import InstrumentChannel, ManualParameter, Parameter
from qcodes.utils.validators import Ints, Numbers

from qcodes_qick.instruments import QickInstrument
from qcodes_qick.parameters import DacDegParameter, DacHzParameter, DacSecParameter


class DACChannel(InstrumentChannel):

    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        assert 0 <= channel <= 6

        self.channel = Parameter(
            name="channel",
            instrument=self,
            label="Channel number",
            initial_value=channel,
        )

        self.nqz = ManualParameter(
            name="nqz",
            instrument=self,
            label="Nyquist zone",
            vals=Ints(1, 2),
            initial_value=1,
        )

        self.pulse_gain = ManualParameter(
            name="pulse_gain",
            instrument=self,
            label="DAC gain",
            vals=Ints(-32768, 32767),
            unit="DAC units",
            initial_value=10000,
        )

        self.pulse_freq = DacHzParameter(
            name="pulse_freq",
            instrument=self,
            label="NCO frequency",
            initial_value=1e9,
        )

        self.pulse_phase = DacDegParameter(
            name="pulse_phase",
            instrument=self,
            label="Pulse phase",
            initial_value=0,
        )

        self.pulse_length = DacSecParameter(
            name="pulse_length",
            instrument=self,
            label="Pulse length",
            initial_value=10e-6,
        )


class ADCChannel(InstrumentChannel):

    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, **kwargs)
        assert 0 <= channel <= 1

        self.channel = Parameter(
            name="channel",
            instrument=self,
            label="Channel number",
            initial_value=channel,
        )

        self.readout_time = ManualParameter(
            name="readout_time",
            instrument=self,
            label="Up time of the ADC readout | Used for timetrace applications",
            vals=Numbers(0, 1000000),
            unit="Clock ticks",
            initial_value=0,
        )
