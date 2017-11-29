# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition

class PID(Actor):
	'''
	Generic PID
	
	Inputs:
		y(queue_length=1,routing="collect-lifo"): Measured value
		y_ref(queue_length=1,routing="collect-lifo"): Reference point
	Outputs:
		v: Control value 
	'''

	@manage(['td', 'ti', 'tr', 'kp', 'ki', 'kd', 'n' ,'beta', 'i', 'd', 'y_old', 'y_ref', 't_prev']) # 
	def init(self, td=1., ti=5., tr=10., kp=-.2, ki=0., kd=0., n=10., beta=1.):
		self.td = td
		self.ti = ti
		self.tr = tr
		self.kp = kp
		self.ki = ki 
		self.kd = kd 
		self.n = n
		self.beta = beta

		self.i = 0.
		self.d = 0.

		self.y_old = 0.
		self.y_ref = 0.

		self.time = None

		self.setup()

		self.t_prev = self.time.timestamp()

	def setup(self):
		self.use('calvinsys.native.python-time', shorthand='time')
		self.time = self['time']

	def did_migrate(self):
		self.setup()

	@condition(['y'],['v'])
	def evaluate(self, y):
		# Time management - for event based controll 
		t = self.time.timestamp()# ms?
		dt = t-self.t_prev
		self.t_prev = t

		# 
		ad = self.td / (self.td + self.n*dt)
		bd = self.kd * ad * self.n

		# e
		e = self.y_ref - y

		# D
		self.d = ad*self.d - bd*(y - self.y_old)

		# Control signal
		v = self.kp * (self.beta * self.y_ref - y) + self.i + self.d

		# I
		self.i += (self.ki * dt/ self.ti) * e * (dt / self.tr) * (y-v)

		# Update state
		self.y_old = y

		self.monitor_value = v

		return (v, )

	@condition(['y_ref'],[])
	def set_ref(self, y_ref):
		self.y_ref = y_ref

	action_priority = (evaluate, set_ref)
	requires = ['calvinsys.native.python-time']
