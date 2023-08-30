import qcodes as qc
from qick import *
import numpy as np

print("hello")
print("hello")
print("hello")
print("hello")
print("hello")


class SweepProgram(RAveragerProgram):

    def __init__(self, soccfg, cfg, sweep_param):
        """
        Constructor for the RAveragerProgram, calls make program at the end so for classes that inherit from this if you want it to do something before the program is made and compiled either do it before calling this __init__ or put it in the initialize method.
        """
        super().__init__(soccfg)
        self.cfg = cfg
        self.make_program()
        self.reps = cfg['reps']
        self.expts = cfg['expts']
        self.sweep_param = sweep_param

        if "rounds" in cfg:
            self.rounds = cfg['rounds']

    #Hardware loop sweep
    def initialize(self):
        cfg=self.cfg   

        # set the nyquist zone
        self.declare_gen(ch=cfg["res_ch"], nqz=1)

        self.r_rp=self.ch_page(self.cfg["res_ch"])     # get register page for res_ch
        self.r_gain=self.sreg(cfg["res_ch"], "gain")   # Get gain register for res_ch
        self.r_freq=self.sreg(cfg["res_ch"], "freq")   # Get gain register for res_ch


        self.sweepable_registers = [self.r_gain, self.r_freq]
        
        #configure the readout lengths and downconversion frequencies
        self.declare_readout(ch=cfg["ro_ch"], length=self.cfg["readout_length"],
                             freq=self.cfg["pulse_freq"], gen_ch=cfg["res_ch"])
        
        freq=self.freq2reg(cfg["pulse_freq"], gen_ch=cfg["res_ch"], ro_ch=cfg["ro_ch"])  # convert frequency to dac frequency (ensuring it is an available adc frequency)
        self.set_pulse_registers(ch=cfg["res_ch"], style="const", freq=freq, phase=0, gain=cfg["start"], 
                                 length=cfg["length"])
        self.synci(200)  # give processor some time to configure pulses

    def body(self):        
        self.measure(pulse_ch=self.cfg["res_ch"], 
             adcs=[self.cfg["ro_ch"]],
             adc_trig_offset=self.cfg["adc_trig_offset"],
             wait=True,
             syncdelay=self.us2cycles(self.cfg["relax_delay"]))        
        
    def update(self):
        if self.sweep_param == "pulse_gain":
            self.mathi(self.r_rp, self.r_gain, self.r_gain, '+', self.cfg["step"]) # update gain of the pulse
        elif self.sweep_param == "pulse_freq":
            self.mathi(self.r_rp, self.r_freq, self.r_freq, '+', self.cfg["step"]) # update gain of the pulse


def single_sweep(sweep_param, sweep_range, soc, experiment, soccfg): 
    #Runs the SingleToneSpectroscopyProgram with frequencies defined in freqs
    possible_sweep_params = ["pulse_freq", "pulse_gain"]
    
    #Configure qick config
    config={"res_ch":6, # --Fixed
        "ro_ch":0, # --Fixed
        "relax_delay":1, # --Fixed
        "res_phase":0, # --Fixed
        "pulse_style": "const", # --Fixed
        "length":100, # [Clock ticks]        
        "readout_length":200, # [Clock ticks]
        "pulse_gain":0, # [DAC units]
        "pulse_freq": 100, # [MHz]
        "adc_trig_offset": 100, # [Clock ticks]
        "reps":50, 
        # New variables
        "expts": 20,
        "start":0, # [DAC units]
        "step":100 
       }

    if sweep_param not in possible_sweep_params:
        print("Invalid sweep parameter")
        return
    else
        #Problematic currently, as there is not a way to fully configure other
        #parameters

        #Here is another place where we need a more comprehensive input validation
        config[sweep_param] = sweep_range[0]
        try:
            config[step] = (sweep_range[-1] - sweep_range[0] )/len(sweep_range)
            config[start] = sweep_range[0]
        except:
            print("Invalid sweep parameter")

    #Create manual parameter for data gathering
    sweep_param_object = qc.ManualParameter(sweep_param, instrument = None, initial_value = sweep_range[0])
    
    #Set up the qc experiment setup
    experiment = qc.load_or_create_experiment(
        experiment_name="zcu_qcodes_test", sample_name="single_sweep")

    meas = qc.Measurement(exp=experiment)
    meas.register_parameter(sweep_param_object)
    meas.register_custom_parameter("avg_i", setpoints=(sweep_param_object,))
    meas.register_custom_parameter("avg_q", setpoints=(sweep_param_object,))
    
    
    #Run the experiment
    with meas.run() as datasaver:

        #Problem with getting this param
        prog = SweepProgram(soccfg, config, sweep_param)

        #The actual qick measurement happens here, as defined by SingleToneSpectroscopyProgram
        avg_i, avg_q = prog.acquire(soc, load_pulses=True)

        #Compile data in QCoDeS style.
        datasaver.add_result((sweep_param_object, f), ("avg_i", avg_i), ("avg_q", avg_q))
    
    run_id = datasaver.dataset.captured_run_id
    dataset = datasaver.dataset

    #If I want to plot or something.
    return dataset

#Initialize qick 
soc = QickSoc()
soccfg = soc

#Initialize database
qc.initialise_or_create_database_at("./zcu_test_data.db")

#Run the experiment -- frequency is in megaherz (see qick example)
output = single_sweep("pulse_freq", np.linspace(4800, 6300, 40), soc, experiment, soccfg)
