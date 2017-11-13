# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition

class PI_BnB(Actor):
	'''
	Super simple PI implementation for the Ball'n'Beam setup.
	
	Inputs:
		y: Measured value
		y_ref: Reference point
	Outputs:
		v: Control value
	'''

	@manage(['ti', 'tr', 'k', 'beta', 'y_ref']) # 
	def init(self, ti=0., tr=1., k=1., beta=1.): # Default parameter values from lab java code
		self.ti = ti
		self.tr = tr
		self.k = k 
		self.beta = beta

		self.y_ref = 0.

	@condition(['y'],['v'])
	def evaluate(self, y):
		# Control signal
		v = self.k * (self.beta * self.y_ref - y)
	
		self.monitor_value = v	

		return (v, )

	@condition(['y_ref'],[])
	def set_ref(self, y_ref):
		self.y_ref = y_ref

	action_priority = (evaluate, set_ref)
	requires = []
