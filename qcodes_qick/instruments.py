from __future__ import annotations

from typing import TYPE_CHECKING

import qick
from qcodes import ChannelTuple, Instrument
from qcodes.parameters import Parameter
from qick.asm_v2 import MultiplexedGenManager, QickProgramV2, StandardGenManager
from qick.pyro import make_proxy

from qcodes_qick.channels import AdcChannel, DacChannel
from qcodes_qick.channels_v2 import AdcChannel as AdcChannelV2
from qcodes_qick.channels_v2 import DacChannel as DacChannelV2
from qcodes_qick.muxed_dac import MuxedDacChannel

if TYPE_CHECKING:
    from qcodes_qick.parameters_v2 import SweepableParameter


class QickInstrument(Instrument):
    def __init__(self, ns_host: str, ns_port=8888, name="QickInstrument", **kwargs):
        super().__init__(name, **kwargs)

        # Use the IP address and port of the Pyro4 nameserver to get:
        #   soc: Pyro4.Proxy pointing to the QickSoc object on the board
        #   soccfg: QickConfig containing the current configuration of the board
        self.soc, self.soccfg = make_proxy(ns_host, ns_port)

        # set of all parameters which have been assigned a QickSweep object
        self.swept_parameters: set[SweepableParameter] = set()

        assert len(self.soccfg["tprocs"]) == 1
        tproc_type = self.soccfg["tprocs"][0]["type"]
        if tproc_type == "axis_tproc64x32_x8":
            tproc_version = 1
        elif tproc_type == "qick_processor":
            tproc_version = 2
        else:
            raise NotImplementedError(f"unsupported tProc type: {tproc_type}")

        self.tproc_version = Parameter(
            name="tproc_version",
            instrument=self,
            label="tProc version",
            initial_cache_value=tproc_version,
        )

        if tproc_version == 1:
            dac_list = []
            for n in range(len(self.soccfg["gens"])):
                dac_list.append(DacChannel(self, f"dac{n}", n))
            self.dacs = ChannelTuple(
                parent=self,
                name="dacs",
                chan_type=DacChannel,
                chan_list=dac_list,
            )
            adc_list = []
            for n in range(len(self.soccfg["readouts"])):
                adc_list.append(AdcChannel(self, f"adc{n}", n))
            self.adcs = ChannelTuple(
                parent=self,
                name="adcs",
                chan_type=AdcChannel,
                chan_list=adc_list,
            )

        elif tproc_version == 2:
            dac_list = []
            for n in range(len(self.soccfg["gens"])):
                dac_type = self.soccfg["gens"][n]["type"]
                manager_class = QickProgramV2.gentypes[dac_type]
                if manager_class == StandardGenManager:
                    dac_list.append(DacChannelV2(self, f"dac{n}", n))
                elif manager_class == MultiplexedGenManager:
                    dac_list.append(MuxedDacChannel(self, f"dac{n}", n))
                else:
                    raise NotImplementedError(f"unsupported DAC type: {dac_type}")
            self.dacs = ChannelTuple(
                parent=self,
                name="dacs",
                chan_type=DacChannelV2,
                chan_list=dac_list,
            )
            adc_list = []
            for n in range(len(self.soccfg["readouts"])):
                adc_list.append(AdcChannelV2(self, f"adc{n}", n))
            self.adcs = ChannelTuple(
                parent=self,
                name="adcs",
                chan_type=AdcChannelV2,
                chan_list=adc_list,
            )

        self.add_submodule("dacs", self.dacs)
        self.add_submodule("adcs", self.adcs)

    def cycles2sec_tproc(self, reg: int) -> float:
        """Convert time from the number of tProc clock cycles to seconds."""
        return self.soccfg.cycles2us(reg) / 1e6

    def sec2cycles_tproc(self, sec: float) -> int:
        """Convert time from seconds to the number of tProc clock cycles."""
        return self.soccfg.us2cycles(sec * 1e6)

    def get_idn(self) -> dict[str, str | None]:
        return {
            "vendor": "Xilinx",
            "model": self.soccfg["board"],
            "serial": None,
            "firmware": f"remote QICK library version = {self.soccfg['sw_version']}, local QICK library version = {qick.__version__}, firmware timestamp = {self.soccfg['fw_timestamp']}",
        }
