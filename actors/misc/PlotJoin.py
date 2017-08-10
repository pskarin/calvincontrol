# -*- coding: utf-8 -*-

# William Tärneberg 2017

from calvin.actor.actor import Actor, manage, condition, stateguard

import random as rnd

class PlotJoin(Actor):
	"""
	Pass input after a given delay
	Input :
		val : value 
	Outputs:
		token : anything
	"""

	@manage(['fig','plt','deliminiator'])
	def init(self, fig, plt, deliminiator=':'):
		self.fig = str(fig) 
		self.plt = str(plt)
		self.deliminiator = deliminiator
		self.setup()

	def setup(self):
		self.use('calvinsys.native.python-time', shorthand='time')

	@condition(['val'], ['token'])
	def join(self, val):
		token = self.deliminiator.join( [self.fig, self.plt, str(self['time'].timestamp()), str(val)])
		return (token, )

	action_priority = (join,)
	requires = ['calvinsys.native.python-time']
