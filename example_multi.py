import qcodes as qc
from qcodes.instrument import Instrument
from qick import *
from qick.averager_program import QickSweep
import numpy as np


class MultiVariableSweepProgram(NDAveragerProgram):
    """
    This class performs a hardware loop sweep over one or more registers 
    in the board. The limit is seven registers.
    Refer to: https://qick-docs.readthedocs.io/en/latest/_modules/qick/averager_program.html#NDAveragerProgram


    Methods
    -------
    initialize(self):
        Initializes the program and defines important variables and registers.
        The sweeps are defined by self.add_sweep calls.
    body(self):
        Defines the structure of the actual measurement and will be looped over reps times.
    """
    def initialize(self):
    
        cfg = self.cfg

        #Defining local variables.
        res_ch = cfg["res_ch"]
        freq = self.freq2reg(cfg["pulse_freq"], gen_ch=res_ch, ro_ch=cfg["ro_chs"][0])
        phase = self.deg2reg(cfg["pulse_phase"], gen_ch=res_ch)
        gain = cfg["pulse_gain"]
        sweep_variables = cfg["sweep_variables"]

        #Declare signal generators and readout
        self.declare_gen(ch=cfg["res_ch"], nqz=1, ro_ch=cfg["ro_chs"][0])
        for ch in cfg["ro_chs"]:
            self.declare_readout(ch=ch, length=self.cfg["readout_length"],
                                 freq=self.cfg["pulse_freq"], gen_ch=cfg["res_ch"])
        self.set_pulse_registers(ch=res_ch, style="const", freq=freq, phase=phase, gain=gain, length=cfg["length"])

        for sweep_variable in sweep_variables:
            if sweep_variable == "length":
                pass

                sweep_settings = sweep_variables[sweep_variable]
                #The register containing the pulse length as the last 16 bits is referred to as the "mode" register.
                sweep_register = self.get_gen_reg(cfg["res_ch"], "mode")
                print(sweep_register.init_val)
                self.add_sweep(QickSweep(self, sweep_register, sweep_settings[0], sweep_settings[1], sweep_settings[2]))
            else:
                sweep_settings = sweep_variables[sweep_variable]
                sweep_register = self.get_gen_reg(cfg["res_ch"], sweep_variable)
                self.add_sweep(QickSweep(self, sweep_register, sweep_settings[0], sweep_settings[1], sweep_settings[2]))


        self.synci(200)  #Give processor some time to configure pulses

    def body(self):

        self.measure(pulse_ch=self.cfg["res_ch"],
                     adcs=self.ro_chs,
                     pins=[0],
                     adc_trig_offset=self.cfg["adc_trig_offset"],
                     wait=True,
                     syncdelay=self.us2cycles(self.cfg["relax_delay"]))


class ZCU216MetaInstrument(Instrument):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.soc = QickSoc()

        # add parameters corresponding to settings of the instrument
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
        ...


def multi_sweep(sweep_configuration, soc, soccfg):
    '''
    This function handles input validation and initializing qcodes around the actual measurement.
    It also handles the proper initialization of the config that will be given to a Qick program
    that is called here.

            Parameters:
                    sweep_configuration (dict): Dictionary that contains the sweep variables
                                                characterized by their flag as their key,
                                                and their sweep start value, end value and
                                                step amount as a list as the dict value.

                    soc: The actual QickSoc object. 
                    soccfg: In this case soccfg and soc point to the same object. If using
                    pyro4, then soc is a Proxy object and soccfg is a QickConfig object.
    '''

    #TO DO: add pulse length sweeps
    possible_sweep_params = {"freq":"MHz", "gain":"DAC", "phase":"deg", "length":"us"}

    #Configure qick config
    config = {"res_ch": 6,  # --Fixed
              "ro_chs": [0],  # --Fixed
              "reps": 1,  # --Fixed
              #Set this really large for real time 
              #debugging using an oscilloscope.
              "relax_delay": 10,  # --us

              "length": 20,  # [Clock ticks]
              "readout_length": 100,  # [Clock ticks]
              "pulse_freq": 100,  # [MHz]
              "pulse_gain": 1000,  # [MHz]
              "pulse_phase": 0,  # [MHz]
              "adc_trig_offset": 150,  # [Clock ticks]
              "soft_avgs": 1,
              "sweep_variables": sweep_configuration
          }

    #dimension will refer to the amount dimension of the sweep in the program
    dimension = 0
    sweep_param_objects = []

    #Set up the QCoDeS experiment setup
    experiment = qc.load_or_create_experiment( experiment_name="zcu_qcodes_test", 
                                               sample_name="single_sweep" )
    meas = qc.Measurement(exp=experiment)

    #Create manual parameters for gathering data
    for sweepable_variable in sweep_configuration:

        #Check wether we can actually loop over each parameter
        if sweepable_variable  not in possible_sweep_params.keys():
            print("Invalid sweep parameter")
            return

        #Deifne the manual parameters
        sweep_param_object = qc.ManualParameter(sweepable_variable, 
                instrument = None, unit=possible_sweep_params[sweepable_variable],
                initial_value = sweep_configuration[sweepable_variable][0])

        dimension += 1
        sweep_param_objects.append(sweep_param_object)
        meas.register_parameter(sweep_param_object)
    

    #Define the custom parameters which are dependent on the manual parameters
    meas.register_custom_parameter("avg_i", setpoints=sweep_param_objects.reverse())
    meas.register_custom_parameter("avg_q", setpoints=sweep_param_objects.reverse())
    param_values = []    
    
    #Run the experiment
    with meas.run() as datasaver:

        #Problem with getting this param
        prog = MultiVariableSweepProgram(soccfg, config)
        print(prog)

        #The actual qick measurement happens here, as defined by the program
        expt_pts, avg_i, avg_q = prog.acquire(soc, load_pulses=True)

        #Create tuples containing 1D data of each experiment point of each sweeped variable
        for i in range(dimension):
            param_values.append((sweep_param_objects[i], expt_pts[i]))

        #Get rid of unnecessary outer brackets.
        for i in range(avg_i.ndim-dimension):
            avg_i = np.squeeze(avg_i)
            avg_q = np.squeeze(avg_q)

        datasaver.add_result( *param_values, 
                ("avg_i", avg_i),
                ("avg_q", avg_q))
    
    #Save the run id
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
output = multi_sweep({"phase":[0,10,2],"gain": [10000, 50000, 2],"freq":[100,500,2], "length":[30,500,5] },soc,soccfg)

#Max length for pulse is 152.38095238095238 microseconds
#pulse_registers = ["freq", "phase", "addr", "gain", "mode", "t", "addr2", "gain2", "mode2", "mode3"]
#TO DO: Input validation and unit fixes.
