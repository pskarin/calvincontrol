# -*- coding: utf-8 -*-
import numpy as np

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition, stateguard

class MatrixMultiplier(Actor):
	"""
	Sequentially pass a value from __values__ at __tick__
	Inputs: 
		m1: Matrix one
		m2: Matrix two
	Outputs:
		result: a value from __values__
	"""

	def init(self):
		self.setup()

	def setup(self):
		pass

	@condition(['m1', 'm2'], ['result'])
	def multiply(self, m1, m2):
		result = np.multiply(m1,m2)
		return (result.tolist(), )

	action_priority = (multiply, )
	requires = []