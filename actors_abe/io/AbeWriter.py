# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition

import time
import os

try:
	from ADCDACPi import ADCDACPi
except ImportError:
	print("Failed to import ADCDACPi from python system path")
	print("Importing from parent folder instead")
	try:
		import sys
		sys.path.append('..')
		from ADCDACPi import ADCDACPi
	except ImportError:
		raise ImportError("Failed to import library from parent folder")

P1 = 0.1675
P2 = 1.656

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
	  value : Input value
	"""

	@manage(['channel','gain_factor','adcdac'])
	def init(self, channel, gain_factor=2):
		assert channel in AVAIL_CHA, 'Channel %i not a valid channel. %s' % (channel, AVAIL_CHA)

		self.channel = channel
		self.gain_factor = gain_factor
		
		self.adcdac = None

		self.setup()

	def setup(self):
		self.adcdac = ADCDACPi( self.gain_factor)
		self.adcdac.set_dac_voltage(self.channel, self.down_scale(0.0))

	def down_scale(self, value):
		#result = REFLECTION_FACTOR*(value/SCALE_FACTOR + 1.)
		
		# Calibrated output y = P1 * value + P2
		result = P1*value + P2	
		result = max(min(result, MAX_OUT), 0) 

		return result

	@condition(action_input=("value",))
	def write(self, value):
		assert -10. <= value <= 10. , "The value: %f is not in the value range (-10, 10)" % value

		self.adcdac.set_dac_voltage( self.channel, self.down_scale(value))
		self.monitor_value = value

	action_priority = (write, )
