from qcodes import Instrument
from qick.pyro import make_proxy


class QickInstrument(Instrument):

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)

        # Use the IP address and port of the Pyro4 nameserver to get:
        #   soc: Pyro4.Proxy pointing to the QickSoc object on the board
        #   soccfg: QickConfig containing the current configuration of the board
        soc, soccfg = make_proxy(ns_host="10.0.100.16", ns_port=8888)
