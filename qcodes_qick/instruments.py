from qcodes import ChannelTuple, Instrument

from qcodes_qick.channels import QickAdcChannel, QickDacChannel
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
            chan_type=QickDacChannel,
            chan_list=[
                QickDacChannel(self, f"dac{ch}", ch) for ch in range(self.dac_count)
            ],
        )
        self.adcs = ChannelTuple(
            parent=self,
            name="adcs",
            chan_type=QickAdcChannel,
            chan_list=[
                QickAdcChannel(self, f"adc{ch}", ch) for ch in range(self.adc_count)
            ],
        )

        self.add_submodule("dacs", self.dacs)
        self.add_submodule("adcs", self.adcs)
