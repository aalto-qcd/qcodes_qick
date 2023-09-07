import qcodes as qc
from qcodes.instrument import Instrument
from qick import *
from qick.averager_program import QickSweep
import numpy as np


class ZCU216MetaInstrument(Instrument):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        #self.soc = QickSoc()

        # add parameters corresponding to settings of the instrument
        # that are *independent of the measurement kind*
        # measurement-specific settings (i.e. pulse lengths and so on) belong in the protocol class
        # not entirely sure whether these are independent parameters
        self.add_parameter("reps")
        self.add_parameter("relax_delay")
        self.add_parameter("adc_trig_offset")
        self.add_parameter("soft_avgs")


    def generate_config(self):
        # generate a configuration dict based on self.parameters
        params = self.parameters
        print(params)

zcu = ZCU216MetaInstrument(name="zcu")
zcu.reps(1)
zcu.relax_delay(10)
zcu.adc_trig_offset(150)
zcu.soft_avgs(1)

