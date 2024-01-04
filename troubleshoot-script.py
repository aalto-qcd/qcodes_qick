from metainstruments.ZCUStation import ZCU216Station
from metainstruments.ZCUMetainstrument import ZCU216MetaInstrument
from measurements.Protocols import T1Protocol

import qcodes as qc
from qcodes.instrument import Instrument, ManualParameter
from qcodes.station import Station
from qick import *

import numpy as np
import matplotlib.pyplot as plt





#Initializing the station and the database
qc.initialise_or_create_database_at("./experiment-data/zcu_test_data.db")
station = ZCU216Station()





station.add_DAC_channel(name="Probe", channel=6)
station.add_ADC_channel(name="Readout", channel=0)
station.add_protocol(protocol = T1Protocol("T1_Protocol"))
station.T1_Protocol.print_readable_snapshot()
station.Readout.print_readable_snapshot()
print(station.troubleshoot())

t1p = station.measure_iq(params_and_values = {station.zcu.delay_time: [400,600,2]}, protocol = T1Protocol(), dac_channels = {'probe', station.Probe}, adc_channel = station.Readout )
testdata = qc.load_by_id(t1p).to_xarray_dataset()
plt.plot(testdata["delay_time"], abs(testdata["avg_q"]+1j*testdata["avg_i"]))
plt.show()
