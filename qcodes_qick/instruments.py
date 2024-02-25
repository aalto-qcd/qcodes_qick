from collections.abc import Sequence

from qcodes import ChannelTuple, Instrument, Measurement

from qcodes_qick.channels import AdcChannel, DacChannel
from qcodes_qick.protocols import HardwareSweep, Protocol, SoftwareSweep
from qick.pyro import make_proxy


class QickInstrument(Instrument):

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)

        # Use the IP address and port of the Pyro4 nameserver to get:
        #   soc: Pyro4.Proxy pointing to the QickSoc object on the board
        #   soccfg: QickConfig containing the current configuration of the board
        soc, self.soccfg = make_proxy(ns_host="10.0.100.16", ns_port=8888)

        self.dac_count = len(self.soccfg["gens"])
        self.adc_count = len(self.soccfg["readouts"])

        self.dacs = ChannelTuple(
            parent=self,
            name="dacs",
            chan_type=DacChannel,
            chan_list=[
                DacChannel(self, f"dac{ch}", ch) for ch in range(self.dac_count)
            ],
        )
        self.adcs = ChannelTuple(
            parent=self,
            name="adcs",
            chan_type=AdcChannel,
            chan_list=[
                AdcChannel(self, f"adc{ch}", ch) for ch in range(self.adc_count)
            ],
        )

        self.add_submodule("dacs", self.dacs)
        self.add_submodule("adcs", self.adcs)

    def cycles2sec_tproc(self, reg: int) -> float:
        """Convert time from the number of tProc clock cycles to seconds"""
        return self.soccfg.cycles2us(reg) / 1e6

    def sec2cycles_tproc(self, sec: float) -> int:
        """Convert time from seconds to the number of tProc clock cycles"""
        return self.soccfg.us2cycles(sec * 1e6)


    def measure_iq(
        self,
        software_sweeps: Sequence[SoftwareSweep],
        hardware_sweeps: Sequence[HardwareSweep],
        protocol: Protocol,
        dac_channels: dict[str, Instrument],
        adc_channels: dict[str, Instrument],
        experiment,
    ):
        """
        This function initializes and runs an IQ measurement.

            Parameters:
                    params_and_values (dict):
                    Dictionary that contains the sweep variables
                    as qcodes parameters, with keys being a list
                    containing the measurement start point, end point
                    and the step count.
                    protocol: the protocol object used in the measurement

            return: QCoDeS run id, corresponding to the measurement
                    (if succesful).
        """

        if protocol not in self.components.values():
            raise Exception("Protocol not defined as an instrument")

        # Here we want to validate the given data, which is protocol dependent.
        io_data = {**dac_channels, **adc_channels}
        protocol.set_io(io_data)
        protocol.validate_params(params_and_values)

        # After input validation, we want to
        # Configure the default config that will remain constant through the measurement

        sweep_param_objects = []
        sweep_configuration = {}

        # initialize qcodes

        meas = Measurement(exp=experiment)

        # Create manual parameters for gathering data
        for parameter, values in params_and_values.items():
            sweep_param_objects.append(parameter)
            meas.register_parameter(parameter, paramtype="array")

        # Define the custom parameters which are dependent on the manual parameters
        meas.register_custom_parameter(
            "avg_i", setpoints=sweep_param_objects, paramtype="array"
        )
        meas.register_custom_parameter(
            "avg_q", setpoints=sweep_param_objects, paramtype="array"
        )

        result_param_values = []

        # The qcodes experiment, surrounding the qick program is contained here.
        with meas.run() as datasaver:

            # Initialize the
            program_base_config, sweep_parameter_list = protocol.initialize_qick_config(
                params_and_values
            )

            # Run the qick program, as defined by the protocol and params_and_values
            expt_pts, avg_i, avg_q = protocol.run_program(
                self.zcu.soc, program_base_config
            )

            # Divide the expt_pts array into individual measurement points
            # for each sweepable variable.
            for i in range(len(sweep_parameter_list)):
                result_param_values.append((sweep_parameter_list[i], expt_pts[i]))

            datasaver.add_result(
                ("avg_i", avg_i), ("avg_q", avg_q), *result_param_values
            )

        # Return the run_id
        run_id = datasaver.dataset.captured_run_id
        return run_id
