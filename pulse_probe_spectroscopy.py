from qick import *

class PulseProbeSpectroscopyProgram(RAveragerProgram):
    def initialize(self):
        cfg=self.cfg

        #Qubit refers to the probe pulse
        #Res refers to readout
        #Cavity refers to the low power resonant probe

        #Defining local variables for qubit probing and readout.
        #The channel for the qubit probing is the channel corresponding
        #to the default pulse variables (pulse_lenght, pulse_phase, etc.)
        qubit_ch = cfg["qubit_ch"]
        probe_freq = self.freq2reg(cfg["pulse_freq"], gen_ch=qubit_ch, ro_ch=cfg["res_ch"])
        probe_phase = self.deg2reg(cfg["pulse_phase"], gen_ch=qubit_ch)
        probe_gain = cfg["pulse_gain"]
        probe_length = self.us2cycles(cfg['pulse_length'], gen_ch=qubit_ch)
        
        #Get the start and step count of the freq sweep
        freq_sweep = cfg["sweep_variables"]["pulse_freq"]
        cfg["expts"] = freq_sweep[2]
        cfg["start"] = freq_sweep[0]
        step_size = round((freq_sweep[1]-freq_sweep[0])/freq_sweep[2])
        cfg["step"] = step_size


        self.declare_gen(ch=cfg["cavity_ch"], nqz=1) #Cavity resonant probe
        self.declare_gen(ch=qubit_ch, nqz=cfg["nqz"]) #Qubit probe

        self.declare_readout(ch=cfg["res_ch"], length=cfg["readout_length"],
                             freq=cfg["cavity_freq"], gen_ch=cfg["cavity_ch"])

        #Find register pages
        self.q_rp=self.ch_page(qubit_ch)     
        self.r_freq=self.sreg(qubit_ch, "freq")   

        # Get dac register value for cavity frequecy 
        cavity_freq=self.freq2reg(cfg["cavity_freq"], gen_ch=cfg["cavity_ch"], ro_ch=cfg["res_ch"]) 

        #Get start and step size frequencies
        self.f_start = self.freq2reg(freq_sweep[0], gen_ch=cfg["qubit_ch"])  
        self.f_step = self.freq2reg(step_size, gen_ch=cfg["qubit_ch"])

        # add qubit and readout pulses to respective channels
        self.set_pulse_registers(ch=qubit_ch, style="const", freq=self.f_start, phase=probe_phase, gain=probe_gain,
                                 length=probe_length)

        self.set_pulse_registers(ch=cfg["cavity_ch"], style="const", freq=cavity_freq, phase=cfg["cavity_phase"], gain=cfg["cavity_gain"],
                                 length=cfg["readout_length"])

        self.sync_all(self.us2cycles(200))

    def body(self):
        self.pulse(ch=self.cfg["qubit_ch"])  #play probe pulse
        self.sync_all(self.us2cycles(0.05)) # align channels and wait 50ns

        #trigger measurement, play measurement pulse, wait for qubit to relax
        self.measure(pulse_ch=self.cfg["cavity_ch"],
             adcs=[0],
             adc_trig_offset=self.cfg["adc_trig_offset"],
             wait=True,
             syncdelay=self.us2cycles(self.cfg["relax_delay"]))

    def update(self):
        self.mathi(self.q_rp, self.r_freq, self.r_freq, '+', self.f_step) # update frequency list index
