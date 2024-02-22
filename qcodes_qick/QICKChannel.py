from qcodes.instrument import InstrumentBase, ManualParameter
from qcodes.utils.validators import Ints, Numbers


class DACChannel(InstrumentBase):

    def __init__(self, name: str, channel_number: int, **kwargs):
        """
        As we initialize the metainstrument, each of the gettable and settable
        parameters are defined and initialized. All parameters receive some
        initial value, but those that initial values corresponding to variables
        that are sweeped over are overwritten.
        """

        self.isDAC = True
        self.isADC = False

        super().__init__(name)

        self.sensible_defaults = {
            "nqz": 1,  # -- First nyquist zone
            "pulse_gain": 5000,  # -- DAC units
            "pulse_phase": 0,  # -- Degrees
            "pulse_freq": 500,  # -- MHz
            "pulse_length": 10,
        }  # -- us

        self.add_parameter(
            "channel",
            parameter_class=ManualParameter,
            label="Channel number",
            vals=Ints(*[0, 6]),
            initial_value=channel_number,
        )

        self.add_parameter(
            "nqz",
            parameter_class=ManualParameter,
            label="Nyquist zone",
            vals=Ints(1, 2),
            initial_value=1,
        )

        self.add_parameter(
            "pulse_gain",
            parameter_class=ManualParameter,
            label="DAC gain",
            vals=Numbers(*[0, 40000]),
            unit="DAC units",
            initial_value=5000,
        )

        self.add_parameter(
            "pulse_freq",
            parameter_class=ManualParameter,
            label="NCO frequency",
            vals=Numbers(*[0, 9000]),
            unit="MHz",
            initial_value=500,
        )

        self.add_parameter(
            "pulse_phase",
            parameter_class=ManualParameter,
            label="Pulse phase",
            vals=Ints(*[0, 360]),
            unit="deg",
            initial_value=0,
        )

        self.add_parameter(
            "pulse_length",
            parameter_class=ManualParameter,
            label="Pulse length",
            vals=Numbers(*[0, 150]),
            unit="us",
            initial_value=10,
        )

    def ask(self, cmd):
        pass


class ADCChannel(InstrumentBase):

    def __init__(self, name: str, channel_number: int, **kwargs):
        """
        As we initialize the metainstrument, each of the gettable and settable
        parameters are defined and initialized. All parameters receive some
        initial value, but those that initial values corresponding to variables
        that are sweeped over are overwritten.
        """

        super().__init__(name)

        self.isDAC = False
        self.isADC = True

        self.add_parameter(
            "channel",
            parameter_class=ManualParameter,
            label="Channel number",
            vals=Ints(*[0, 1]),
            initial_value=channel_number,
        )

        self.add_parameter(
            "readout_time",
            parameter_class=ManualParameter,
            label="Up time of the ADC readout | Used for timetrace applications",
            vals=Numbers(*[0, 1000000]),
            unit="Clock ticks",
            initial_value=0,
        )

    def ask(self, cmd):
        pass
