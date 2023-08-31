import qcodes as qc
from qcodes.instrument import Instrument
from qick import *
import numpy as np

class SweepProgram(RAveragerProgram):

    #Hardware loop sweep
    def initialize(self):
        cfg=self.cfg   

        # set the nyquist zone
        self.declare_gen(ch=cfg["res_ch"], nqz=1)

        self.r_rp=self.ch_page(self.cfg["res_ch"])     # get register page for res_ch
        self.r_gain=self.sreg(cfg["res_ch"], "gain")   # Get gain register for res_ch
        self.r_freq=self.sreg(cfg["res_ch"], "freq")   # Get freq register for res_ch


        self.sweepable_registers = [self.r_gain, self.r_freq]
        
        #configure the readout lengths and downconversion frequencies
        self.declare_readout(ch=cfg["ro_ch"], length=self.cfg["readout_length"],
                             freq=self.cfg["pulse_freq"], gen_ch=cfg["res_ch"])
        
        freq=self.freq2reg(cfg["pulse_freq"], gen_ch=cfg["res_ch"], ro_ch=cfg["ro_ch"])  # convert frequency to dac frequency (ensuring it is an available adc frequency)
        self.set_pulse_registers(ch=cfg["res_ch"], style="const", freq=freq, phase=0, gain=cfg["pulse_gain"], 
                                 length=cfg["length"])
        self.synci(200)  # give processor some time to configure pulses

    def body(self):        
        self.measure(pulse_ch=self.cfg["res_ch"], 
             adcs=[self.cfg["ro_ch"]],
             adc_trig_offset=self.cfg["adc_trig_offset"],
             wait=True,
             syncdelay=self.us2cycles(self.cfg["relax_delay"]))        
        
    def update(self):
        if self.cfg["sweep_param"] == "pulse_gain":
            self.mathi(self.r_rp, self.r_gain, self.r_gain, '+', self.cfg["step"]) # update gain of the pulse

        elif self.cfg["sweep_param"] == "pulse_freq":
            self.mathi(self.r_rp, self.r_freq, self.r_freq, '+', self.cfg["step"]) # update freq of the pulse

class MultiVariableSweepProgram(NDAveragerProgram):
    def initialize(self):
    
        cfg = self.cfg
        res_ch = cfg["res_ch"]

        self.declare_gen(ch=cfg["res_ch"], nqz=1, ro_ch=cfg["ro_chs"][0])

        for ch in cfg["ro_chs"]:
            self.declare_readout(ch=ch, length=self.cfg["readout_length"],
                                 freq=self.cfg["pulse_freq"], gen_ch=cfg["res_ch"])

        # convert frequency to DAC frequency (ensuring it is an available ADC frequency)
        freq = self.freq2reg(cfg["pulse_freq"], gen_ch=res_ch, ro_ch=cfg["ro_chs"][0])
        phase = self.deg2reg(cfg["pulse_phase"], gen_ch=res_ch)
        gain = cfg["pulse_gain"]

        self.set_pulse_registers(ch=res_ch, style="const", freq=freq, phase=phase, gain=gain, length=cfg["length"])
        
        # ---------- sweep defination starts from here -----------------
        # get gain, frequency and phase registers of the generator channel 
        # Meaby does not work if we don't do class variables
        #self.res_r_gain = self.get_gen_reg(cfg["res_ch"], "gain")
        #self.res_r_phase = self.get_gen_reg(cfg["res_ch"], "phase")
        #self.res_r_freq = self.get_gen_reg(cfg["res_ch"], "freq")

        # add desired sweeps
        for sweep_variable in sweep_variables:
            sweep_settings = sweep_variables[sweep_variable]
            sweep_register = self.get_gen_reg(cfg["res_ch"], sweep_variable)
            self.add_sweep(QickSweep(self, sweep_register, sweep_settings[0], sweep_settings[1], sweep_settings[2]))


        self.synci(200)  # give processor some time to configure pulses

    def body(self):
        self.measure(pulse_ch=self.cfg["res_ch"],
                     adcs=self.ro_chs,
                     pins=[0],
                     adc_trig_offset=self.cfg["adc_trig_offset"],
                     wait=True,
                     syncdelay=self.us2cycles(self.cfg["relax_delay"]))

# unlike the RAveragerProgram, here we only have initialize() and body() part in the program, and the register update 
# parts (which will be run after each body) are programed in QickSweep objects.

class ZCU216MetaInstrument(Instrument):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.soc = QickSoc()

        # add parameters corresponding to settinsg of the instrument
        # that are *independent of the measurement kind*
        # measurement-specific settings (i.e. pulse lengths and so on) belong in the protocol class
        self.add_parameter("res_ch")
        self.add_parameter("ro_chs")
        self.add_parameter("reps")
        self.add_parameter("relax_delay")
        self.add_parameter("readout_length")
        self.add_parameter("adc_trig_offset")
        self.add_parameter("soft_avgs")

    def generate_config(self) -> dict:
        # generate a configuration dict based on self.parameters
        ...

    def add_paramteter(self, ):


def multi_sweep(sweep_configuration, soc, soccfg):


    possible_sweep_params = {"freq":"MHz", "gain":"DAC", "phase":"deg"]

    #Configure qick config
    config = {"res_ch": 6,  # --Fixed
          "ro_chs": [0],  # --Fixed
          "reps": 1,  # --Fixed
          "relax_delay": 1.0,  # --us
          "length": 50,  # [Clock ticks]
          "readout_length": 100,  # [Clock ticks]
          "pulse_freq": 100,  # [MHz]
          "pulse_gain": 100,  # [MHz]
          "pulse_phase": 0,  # [MHz]
          "adc_trig_offset": 150,  # [Clock ticks]
          "soft_avgs": 1,
          }

    sweep_param_objects = []

    #Set up the qc experiment setup
    experiment = qc.load_or_create_experiment(
        experiment_name="zcu_qcodes_test", sample_name="single_sweep")
    meas = qc.Measurement(exp=experiment)

    #Create manual parameters for data gathering
    for sweepable_variable in sweep_configuration:

        if sweep_param not in possible_sweep_params:
            print("Invalid sweep parameter")
            return

        sweep_param_object = qc.ManualParameter(sweepable_variable, instrument = None, unit=possible_sweep_params[sweepable_variable],
                initial_value = sweep_configuaration[sweepable_variable][0])

        sweep_param_objects.append(sweep_param_object)

        meas.register_parameter(sweep_param_object)
    

    meas.register_custom_parameter("avg_i", setpoints=sweep_param_objects)
    meas.register_custom_parameter("avg_q", setpoints=sweep_param_objects)
    
    
    #Run the experiment
    with meas.run() as datasaver:

        #Problem with getting this param
        prog = MultiVariableSweepProgram(soccfg, config)

        #The actual qick measurement happens here, as defined by the program
        expt_pts, avg_i, avg_q = prog.acquire(soc, load_pulses=True)

        print(config)
        print(expt_pts)
        #Compile data in QCoDeS style.
        datasaver.add_result((sweep_param_object, expt_pts), 
                ("avg_i", np.reshape(avg_i, len(sweep_range))),
                ("avg_q", np.reshape(avg_q, len(sweep_range))))
    
    run_id = datasaver.dataset.captured_run_id
    dataset = datasaver.dataset

    #If I want to plot or something.
    return dataset





def single_sweep(sweep_param, sweep_range, soc, soccfg): 
    #Runs the SingleToneSpectroscopyProgram with frequencies defined in freqs
    

    config={"res_ch":6, # --Fixed
        "ro_ch":0, # --Fixed
        "relax_delay":0.01, # --Fixed
        "res_phase":0, # --Fixed
        "pulse_style": "const", # --Fixed
        "length":10, # [Clock ticks]        
        "readout_length":1000, # [Clock ticks]
        #Defaults, one of which will be overwritten
        "pulse_gain": 10000, # [DAC units]
        "pulse_freq": 100, # [MHz]

        "adc_trig_offset": 170, # [Clock ticks]
        "reps": 1, 
        # New variables
        "expts": len(sweep_range),
       }

    if sweep_param not in possible_sweep_params:
        print("Invalid sweep parameter")
        return
    else:
        #Problematic currently, as there is not a way to fully configure other
        #parameters

        #Here is another place where we need a more comprehensive input validation
        config[sweep_param] = round(sweep_range[0])
        config["start"] = round(sweep_range[0])
        config["sweep_param"] = sweep_param
        try:
            config['step'] = round((sweep_range[-1] - sweep_range[0] )/len(sweep_range))
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
        prog = SweepProgram(soccfg, config)

        #The actual qick measurement happens here, as defined by the program
        expt_pts, avg_i, avg_q = prog.acquire(soc, load_pulses=True)

        #Compile data in QCoDeS style.
        print(config)
        print(expt_pts)
        datasaver.add_result((sweep_param_object, expt_pts), ("avg_i", np.reshape(avg_i, len(sweep_range))), ("avg_q", np.reshape(avg_q, len(sweep_range))))
    
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
output = multi_sweep({"gain": [100, 500, 20]}, soc, soccfg)
