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
NEG_COMP = 0 #-0.04
POS_COMP = 0 #1.1

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
	  value : Input value
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

	def did_migrate(self):
		self.setup()

	def down_scale(self, value):
		#result = REFLECTION_FACTOR*(value/SCALE_FACTOR + 1.)
		
		# Calibrated output y = P1 * value + P2
		result = P1*value + P2	
		result = max(min(result, MAX_OUT), 0) 

		return result

	@condition(action_input=("value",))
	def write(self, value_ts):
		value, ts, tick = value_ts
		if value < 0:
			value += NEG_COMP
		else:
			value += POS_COMP
		if not fake:
			assert -10. <= value <= 10. , "The value: %f is not in the value range (-10, 10)" % value
			self.adcdac.set_dac_voltage( self.channel, self.down_scale(value))
		myts = self.time.timestamp()
		diffs = []
		for t in ts:
			diffs.append(myts-t)
#		if max(diffs) > 0.1:
#		self.monitor_value_0 = diffs
		self.monitor_value = (myts,)+ts

	action_priority = (write, )
	requires = ['calvinsys.native.python-time']