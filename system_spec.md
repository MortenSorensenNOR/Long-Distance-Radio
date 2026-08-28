# Overall system architecture:
1) control and ADC/DAC board. this board has a usb c port, potentially ethernet port, a microcontroller (which talks to the host),
ideally this can handle standard ethernet trafic as well as usb trafic over the usb c cable, an FPGA that reads and writes the the ADCs and DACs as well as doing the digital singal processing for converting
I/Q samples to finished dataframes for the microcontroller, as well as dataframes -> I/Q samples for TX. overall scheduling is handled by the microcontroller. one simultanious two channel ADC and likewise
DAC send and recieve I and Q streams. 2) mixer board. on transmit it takes a filtered version of the dac I/Q signals, takes an LO from the LO board, mixes up from baseband to 869.4 + 0.25 / 2 MHz. There may 
be a filter between the DAC and the mixer, and there is going to be a bandpass filter between the mixer and the output port. on the receive side the rf from the LNA board is sent
into the mixer, giving out I and Q. each are then filtered and then amplified, before being sent to the control/ADC/DAC board. 4) LO BOARD. this generates the LO that is used for mixing up and down. It has 
the option for an internal oscillator, but for the system operation it will take it's reference clock from the clock board. 5) CLOCK BOARD. this generates the 100 MHz clock used for both the LO board as well
as generating the trigger/acquisition/update of the ADCs and DACs. it has a frequency and phase stable TCXO at 100 MHz (~0.5 ppm) sent into a clock buffer for sending throughout the system. 6) LNA BOARD. this board takes 
the incomming rf, sends it through a SAW filter that has been specially chosen to exhibit extra attenuation at 850-862 or so MHz, in order to block cell phone/4g uplink signals from interferring. Then goes 
through a custom made low noise amplifier, designed by me, TBD, then futher bandpass filtered and sent off to the mixer board. not certain yet if i want to place the last bandpass filter on the LNA board or 
the mixer board. TBD. 7) PA BOARD. self explanitory, takes the mixer board output, bandpass filteres, sends through a power amplifier designed my be, probably class A, B or A/B, something quite linear is the goal,
then filtered again and sent to the antenna. on the lna and pa boards there will be a SPDT switch to turn off and on the RX and TX paths.

The overall system specs should be something like:
- 250 kHz BW between 869.4 MHz and 869.65 MHz
- Using TDD for the initial design constrained by 10% allowed duty cycle, future work will change the operating band and will thusly change duty cycle limit -> FDD? Also l
- The specific band in Fribruksforskriften:
  "(19) Frekvensbåndet 869,400–869,650 MHz tillates brukt som beskrevet i standarden EN 300 220-2. Maksimal tillatt utstrålt effekt er 500 mW e.r.p. Maksimal sendetid er 10 prosent. Sendetiden tillates over 10 prosent dersom det benyttes interferensreduserende tiltak som gir minst samme virkning som teknikker beskrevet i harmoniserte standarder."
- Range of up to 2 km, using directional antennas. 
- Goal of 1 mbps, which needs at least 15 or perhaps 20 dB SNR
- Use OFDM with a relatively small cyclic prefix, simplifying channel equalization
- Stationary system, only objects inside the radio link are moving
- NLOS, this is the one that makes things somewhat complicated, necessitating higher SNR to account for fading
- Nice to have is to be able to stream raw I/Q samples in and out of the system at line speed
- Make a cool fucking radio from scratch :)

# Parts already chosen:
- TB612-100.0M TCXO @ 100Mhz with 0.5 ppm stability and excellent phase noise
- LMX2582 PLL/VCO cip for generating LO, excellent phase noise

# Parts considered
- FPGA, something like the TZ170J361I2 from efinix
- RP2350, or some other form of dual core arm core, ideally something that can easily integrate with usb c

# Testing of FPGA
- Use cocotb + python + cocotbext-axi to fully test sub-blocks and hole system tests with simulated
  rf performance
