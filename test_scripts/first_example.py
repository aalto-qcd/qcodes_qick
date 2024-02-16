import qcodes as qc
from qick import *
import numpy as np

class SingleToneSpectroscopyProgram(AveragerProgram):
    def initialize(self):
        cfg=self.cfg
        self.declare_gen(ch=cfg["res_ch"], nqz=1) #Readout
        for ch in [0,1]: #configure the readout lengths and downconversion frequencies
            self.declare_readout(ch=ch, length=cfg["readout_length"],
                                 freq=cfg["frequency"], gen_ch=cfg["res_ch"])

        freq=self.freq2reg(cfg["frequency"], gen_ch=cfg["res_ch"], ro_ch=0)  # convert frequency to dac 
                                                                             #frequency (ensuring it is an available adc 
                                                                             # frequency)

        self.set_pulse_registers(ch=cfg["res_ch"], style="const", freq=freq, phase=0, gain=cfg["res_gain"],
                                length=cfg["readout_length"])

        self.synci(200)  # give processor some time to configure pulses

    def body(self):
        self.measure(pulse_ch=self.cfg["res_ch"],
             adcs=[0,1],
             adc_trig_offset=self.cfg["adc_trig_offset"],
             wait=True,
             syncdelay=self.us2cycles(self.cfg["relax_delay"]))  

def run_freq_experiment(freqs, soc, experiment, soccfg): 
    #Runs the SingleToneSpectroscopyProgram with frequencies defined in freqs
    
    #Configure qick config
    hw_cfg={"jpa_ch":5,
            "res_ch":6,
            "qubit_ch":2,
            "storage_ch":0
           }
    readout_cfg={
        "readout_length":soccfg.us2cycles(3.0, gen_ch=5), # [Clock ticks]
        "f_res": 99.775 +0.18, # [MHz]
        "res_phase": 0,
        "adc_trig_offset": 275, # [Clock ticks]
        "res_gain":10000
        }
    qubit_cfg={
        "sigma":soccfg.us2cycles(0.025, gen_ch=2),
        "pi_gain": 11500,
        "pi2_gain":11500//2,
        "f_ge":4743.041802067813,
        "relax_delay":500
    }

    #Redundant except for relax_delay
    expt_cfg={"reps":500, "relax_delay":10,
              "start":95, "step":0.025, "expts":400
             }

    #Compile all configs
    config={**hw_cfg,**readout_cfg,**qubit_cfg,**expt_cfg}
    
    #Create manual frequency parameter for data gathering
    frequency_param_object = qc.ManualParameter('frequency', instrument=None, initial_value = 5e9)
    
    #Set up the qc experiment setup
    meas = qc.Measurement(exp=experiment)
    meas.register_parameter(frequency_param_object)
    meas.register_custom_parameter("avg_i", setpoints=(frequency_param_object,))
    meas.register_custom_parameter("avg_q", setpoints=(frequency_param_object,))
    
    #Run the experiment
    with meas.run() as datasaver:

        # Loop over desired frequencies 
        for f in freqs:

            config["frequency"] = f
            prog = SingleToneSpectroscopyProgram(soccfg, config)

            #The actual qick measurement happens here, as defined by SingleToneSpectroscopyProgram
            avg_i, avg_q = prog.acquire(soc, load_pulses=True)

            #Compile data in QCoDeS style.
            datasaver.add_result((frequency_param_object, f), ("avg_i", avg_i), ("avg_q", avg_q))
    
        run_id = datasaver.dataset.captured_run_id
        dataset = datasaver.dataset

    #If I want to plot or something.
    return dataset

#Initialize qick 
soc = QickSoc()
soccfg = soc

#Initialize database
qc.initialise_or_create_database_at("./zcu_test_data.db")
experiment = qc.load_or_create_experiment(
    experiment_name="zcu_qcodes_test",
    sample_name="single_tone"
)

#Run the experiment -- frequency is in megaherz (see qick example)
output = run_freq_experiment(np.linspace(4800, 6300, 40), soc, experiment, soccfg)
