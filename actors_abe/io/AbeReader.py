# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition, stateguard

import time
import os
import sys

try:e
	from ADCDACPi import ADCDACPi
	fake = Fals
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

	Outputs:
	  value : ADC value in volts
	"""

	@manage(['tick', 'channel', 'timer', 'started'])
	def init(self, tick, channel, gain_factor=2, mode=0):
		assert channel in AVAIL_CHA, 'Channel %i not a valid channel. %s' % (channel, AVAIL_CHA)

		self.tick = tick

		self.channel = channel
		self.gain_factor = gain_factor
		self.mode = mode

		self.timer = None 
		self.started = False 

		self.adcdac = None

		self.setup()

	def setup(self):
		self.use('calvinsys.native.python-time', shorthand='time')
		self.use('calvinsys.events.timer', shorthand='timer')
		self.time = self['time']
		if not fake:
			self.adcdac = ADCDACPi( self.gain_factor)
			self.adcdac.set_adc_refvoltage(MAX_OUT)

	def start(self):
		self.timer = self['timer'].repeat(self.tick)
		self.started = True

	def up_scale(self, value):
		#result = SCALE_FACTOR*(value - 1.)/REFLECTION_FACTOR
		 
		# Calibrated output y = P1 * value + P2
		result = P1*value + P2  	

		return result 

	@stateguard(lambda self: not self.started)
	@condition([], [])
	def start_timer(self):
		self.start()

	@stateguard(lambda self: self.timer and self.timer.triggered)
	@condition([], ['value'])
	def trigger(self):
		value = 0.
		if not fake:
			self.timer.ack()
			value = self.up_scale( self.adcdac.read_adc_voltage(self.channel, self.mode))

			self.monitor_value = value 

		return ((value, self.time.timestamp()),)

	action_priority = (start_timer, trigger)
	requires = ['calvinsys.events.timer', 'calvinsys.native.python-time']
