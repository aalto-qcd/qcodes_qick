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





station.add_DAC_channel(name="QubitProbe", channel=6)
station.add_DAC_channel(name="ReadoutProbe", channel=4)
station.add_ADC_channel(name="ReadoutADC", channel=0)
station.add_protocol(protocol = T1Protocol("T1_Protocol"))
#station.print_io_configuration()
#print(station.troubleshoot())

t1p = station.measure_iq(params_and_values = {station.T1_Protocol.variable_delay: [0,300,2]}, protocol = T1Protocol(), dac_channels = {'qubit': station.QubitProbe,'readout': station.ReadoutProbe}, adc_channels = {'adc' : station.ReadoutADC} )
testdata = qc.load_by_id(t1p).to_xarray_dataset()
print(testdata)
