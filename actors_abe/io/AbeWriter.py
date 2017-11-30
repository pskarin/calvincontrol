# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition

import time
import os
import sys

try:
	from ADCDACPi import ADCDACPi
	fake = False
except ImportError:
	print("Failed to import ADCDACPi from python system path")
	fake = True

P1 = 0.165
P2 = 1.65

AVAIL_CHA = [1,2]
MAX_OUT = 3.299
REFLECTION_FACTOR = MAX_OUT/2.
SCALE_FACTOR = 10.

class AbeWriter(Actor):

	"""
	Write to AB Electronics ADC-DAC Pi Zero

	Requires: 
		- Raspberry Pi > model B
		- AB Electronics ADC-DAC Pi Zero
		- Up/Down scale (+-10V) circuit available at ...
		- SPI enabled
		- PySPI Dev
		- AB Electronics python libraries https://github.com/abelectronicsuk/ABElectronics_Python_Libraries.git

	Inputs:
	  value(queue_length=1,routing="collect-lifo") : Input value
	"""

	@manage(['channel','gain_factor'])
	def init(self, channel, gain_factor=2):
		assert channel in AVAIL_CHA, 'Channel %i not a valid channel. %s' % (channel, AVAIL_CHA)

		self.channel = channel
		self.gain_factor = gain_factor
		
		self.adcdac = None

		self.setup()

	def setup(self):
		self.use('calvinsys.native.python-time', shorthand='time')
		self.time = self['time']
		if not fake:
			self.adcdac = ADCDACPi( self.gain_factor)
			self.adcdac.set_dac_voltage(self.channel, self.down_scale(0.0))

	def down_scale(self, value):
		#result = REFLECTION_FACTOR*(value/SCALE_FACTOR + 1.)
		
		# Calibrated output y = P1 * value + P2
		result = P1*value + P2	
		result = max(min(result, MAX_OUT), 0) 

		return result

	@condition(action_input=("value",))
	def write(self, value_ts):
		value, ts = value_ts
		if not fake:
			assert -10. <= value <= 10. , "The value: %f is not in the value range (-10, 10)" % value
			self.adcdac.set_dac_voltage( self.channel, self.down_scale(value))
			self.monitor_value = value
		else:
			sys.stderr.write("write: {}\n".format(value_ts))
#		sys.stderr.write("in-out delta time: {:6.2f}\n".format((self.time.timestamp()-ts)*1000))

	action_priority = (write, )
	requires = ['calvinsys.native.python-time']