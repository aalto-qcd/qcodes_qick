import qcodes as qc
from qcodes.instrument import Instrument, ManualParameter
from qcodes.station import Station

from metainstruments.ZCUStation import ZCU216Station
from metainstruments.ZCUMetainstrument import ZCU216Metainstrument
from measurements.Protocols import Protocol
from measurements.T1Protocol import T1Protocol
from measurements.PulseProbeSpectroscopyProtocol import PulseProbeSpectroscopyProtocol
from measurements.NDSweepProtocol import NDSweepProtocol
from qick import *


import numpy as np
import matplotlib.pyplot as plt




#Initializing the station and the database
qc.initialise_or_create_database_at("./experiment-data/zcu_test_data.db")
station = ZCU216Station()



#Initializing the experiment
experiment = qc.load_or_create_experiment(
                experiment_name="ZCU_QICK_QCODES_TEST",
                sample_name="None")



#At the time of writing, we have connected DACs 2_231 and 0_231 to the adc's and oscilloscopes, these have
#qick channels 6 and 4. The physically connected ADC channel is 0_226. Thus, our configuration will be:
station.add_DAC_channel(name="Probe", channel=6)
station.add_DAC_channel(name="Readout", channel=4)
station.add_ADC_channel(name="ADC", channel=0)


# Initialization of the protocol
vnaprotocol = station.add_protocol(NDSweepProtocol(name='vna'))

station.vna.reps(10)

station.measure_iq(params_and_values = {  station.Probe.pulse_gain: [100, 3000, 10]},
                         protocol = vnaprotocol,
                         dac_channels = {'probe': station.Probe},
                         adc_channels = {'adc' : station.ADC},
                         experiment = experiment)


vnaprotocol = station.add_protocol(PulseProbeSpectroscopyProtocol(name='pps'))

station.measure_iq(params_and_values = {  station.Probe.pulse_freq: [1000, 1100, 100]},
                         protocol = station.pps,
                         dac_channels = {'qubit': station.Probe, 'readout': station.Readout},
                         adc_channels = {'adc' : station.ADC},
                         experiment = experiment)

vnaprotocol = station.add_protocol(T1Protocol(name='T1'))

station.measure_iq(params_and_values = {  station.T1.variable_delay: [0, 300, 1000]},
                         protocol = station.T1,
                         dac_channels = {'qubit': station.Probe, 'readout': station.Readout},
                         adc_channels = {'adc' : station.ADC},
                         experiment = experiment)

