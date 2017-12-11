# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition, stateguard

import time
import os
import sys

try:
	from ADCDACPi import ADCDACPi
	fake = False
except ImportError:
	sys.stderr.write("Failed to import ADCDACPi from python system path\n")
	fake = True

P1 = 6.061
P2 = -10.

AVAIL_CHA = [1,2]
MAX_OUT = 3.299
REFLECTION_FACTOR = MAX_OUT/2.
SCALE_FACTOR = 10.

class AbeReader(Actor):

	"""
	Reads every [tick] seconds from AB Electronics ADC-DAC Pi Zero

	Requires 
		- Raspberry Pi > model B
		- AB Electronics ADC-DAC Pi Zero
		- Up/Down scale (+-10V) circuit available at ...
		- SPI enabled
		- PySPI Dev
		- AB Electronics python libraries https://github.com/abelectronicsuk/ABElectronics_Python_Libraries.git

	Inputs:
	  tick : Clock tick
	Outputs:
	  value : ADC value in volts
	"""

	@manage(['channel'])
	def init(self, channel, gain_factor=2, mode=0):
		assert channel in AVAIL_CHA, 'Channel %i not a valid channel. %s' % (channel, AVAIL_CHA)

		self.channel = channel
		self.gain_factor = gain_factor
		self.mode = mode

		self.adcdac = None

		self.setup()

	def setup(self):
		self.use('calvinsys.native.python-time', shorthand='time')
		self.time = self['time']
		if not fake:
			self.adcdac = ADCDACPi( self.gain_factor)
			self.adcdac.set_adc_refvoltage(MAX_OUT)

	def up_scale(self, value):
		#result = SCALE_FACTOR*(value - 1.)/REFLECTION_FACTOR
		 
		# Calibrated output y = P1 * value + P2
		result = P1*value + P2  	

		return result 

	@condition(['tick'], ['value'])
	def trigger(self, tick):
		value = 0.
		if not fake:
			value = self.up_scale( self.adcdac.read_adc_voltage(self.channel, self.mode))

			self.monitor_value = value 

		return ((value, self.time.timestamp()),)

	action_priority = (trigger,)
	requires = ['calvinsys.native.python-time']
