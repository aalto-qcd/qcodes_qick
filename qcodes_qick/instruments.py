from qcodes import ChannelTuple, Instrument

import qick
from qcodes_qick.channels import AdcChannel, DacChannel
from qick.pyro import make_proxy


class QickInstrument(Instrument):

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)

        # Use the IP address and port of the Pyro4 nameserver to get:
        #   soc: Pyro4.Proxy pointing to the QickSoc object on the board
        #   soccfg: QickConfig containing the current configuration of the board
        self.soc, self.soccfg = make_proxy(ns_host="10.0.100.16", ns_port=8888)

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
    
    def get_idn(self) -> dict[str, str | None]:
        return {
            "vendor": "Xilinx",
            "model": "ZCU216",
            "serial": "",
            "firmware": f"remote QICK library version = {self.soccfg['sw_version']}, local QICK library version = {qick.__version__}",
        }
