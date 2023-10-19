from qick import *

class T1Program(RAveragerProgram):
    def initialize(self):
        cfg=self.cfg

        #Qubit refers to the probe pulse
        #Res refers to readout
        #Cavity refers to the low power resonant probe

        #Defining local variables for qubit probing and readout.
        #The channel for the qubit probing is the channel corresponding
        #to the default pulse variables (pulse_lenght, pulse_phase, etc.)
        qubit_ch = cfg["qubit_ch"]
        probe_gain = cfg["pulse_gain"]
        probe_length = self.us2cycles(cfg['pulse_length'], gen_ch=qubit_ch)

        cavity_freq=self.freq2reg(cfg["cavity_freq"], gen_ch=cfg["cavity_ch"], ro_ch=cfg["res_ch"]) # conver f_res to dac register value
        probe_freq=self.freq2reg(cfg["pulse_freq"], gen_ch=cfg["qubit_ch"])

        t1_sigma = self.us2cycles(cfg["t1_sigma"], qubit_ch)
        cavity_pulse_length = self.us2cycles(cfg['readout_length'], gen_ch=cfg["cavity_ch"])

        #Get the start and step count of the relax delay sweep
        time_sweep = cfg["sweep_variables"]["delay_time"]
        cfg["expts"] = time_sweep[2]
        cfg["start"] = time_sweep[0]
        step_size = (time_sweep[1]-time_sweep[0])/time_sweep[2]
        cfg["step"] = step_size

        #Get register page for qubit_ch
        self.q_rp=self.ch_page(qubit_ch)    
        self.r_wait = 3
        self.regwi(self.q_rp, self.r_wait, self.us2cycles(cfg["start"]))

        self.declare_gen(ch=cfg["cavity_ch"], nqz=1) #Readout
        self.declare_gen(ch=cfg["qubit_ch"], nqz=cfg["nqz"]) #Qubit

        self.declare_readout(ch=cfg["res_ch"], length=cfg["readout_length"],
                             freq=cfg["cavity_freq"], gen_ch=cfg["cavity_ch"])


        # add qubit and readout pulses to respective channels
        self.add_gauss(ch=qubit_ch, name="qubit", sigma=t1_sigma, length=t1_sigma*4)
        self.set_pulse_registers(ch=qubit_ch, style="arb", freq=probe_freq, phase=0, gain=probe_gain,
                                 waveform="qubit")
        self.set_pulse_registers(ch=cfg["cavity_ch"], style="const", freq=cavity_freq, phase=cfg["cavity_phase"], gain=cfg["cavity_gain"],
                                 length=cavity_pulse_length)

        self.sync_all(self.us2cycles(500))

    def body(self):

        #Probe the qubit with the gaussian pulse
        self.pulse(ch=self.cfg["qubit_ch"])  
        self.sync_all()

        #Variable wait time is applied here
        self.sync(self.q_rp,self.r_wait)

        #trigger measurement, play measurement pulse, wait for qubit to relax
        self.measure(pulse_ch=self.cfg["cavity_ch"],
             adcs=[self.cfg["res_ch"]],
             adc_trig_offset=self.cfg["adc_trig_offset"],
             wait=True,
             syncdelay=self.us2cycles(self.cfg["relax_delay"]))

    def update(self):
        self.mathi(self.q_rp, self.r_wait, self.r_wait, '+', self.us2cycles(self.cfg["step"])) # update variable delay
