from qcodes import InstrumentChannel, ManualParameter
from qcodes.utils.validators import Ints, Numbers

from qcodes_qick.instruments import QickInstrument


class DACChannel(InstrumentChannel):

    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, **kwargs)

        self.channel = ManualParameter(
            name="channel",
            instrument=self,
            label="Channel number",
            vals=Ints(0, 6),
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
            vals=Numbers(0, 40000),
            unit="DAC units",
            initial_value=5000,
        )

        self.pulse_freq = ManualParameter(
            name="pulse_freq",
            instrument=self,
            label="NCO frequency",
            vals=Numbers(0, 9000),
            unit="MHz",
            initial_value=500,
        )

        self.pulse_phase = ManualParameter(
            name="pulse_phase",
            instrument=self,
            label="Pulse phase",
            vals=Ints(0, 360),
            unit="deg",
            initial_value=0,
        )

        self.pulse_length = ManualParameter(
            name="pulse_length",
            instrument=self,
            label="Pulse length",
            vals=Numbers(0, 150),
            unit="us",
            initial_value=10,
        )


class ADCChannel(InstrumentChannel):

    def __init__(self, parent: QickInstrument, name: str, channel: int, **kwargs):
        super().__init__(parent, name, **kwargs)

        self.channel = ManualParameter(
            name="channel",
            instrument=self,
            label="Channel number",
            vals=Ints(0, 1),
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
