# -*- coding: utf-8 -*-

# William Tärneberg 2017
import sys
from calvin.actor.actor import Actor, manage, condition

class PID(Actor):
	'''
	Generic PID
	
	Inputs:
		y(routing="collect-single-slot"): Measured value
		y_ref(routing="collect-single-slot"): Reference point
	Outputs:
		v: Control value 
	'''

	@manage(['td', 'ti', 'tr', 'kp', 'ki', 'kd', 'n' ,'beta', 'i', 'd', 'y_old', 'y_ref', 'y_prev_t', 'ref_prev_t', 'ts_fwd_ref'])
	def init(self, td=1., ti=5., tr=10., kp=-.2, ki=0., kd=0., n=10., beta=1., ts_fwd_ref=False):
		self.td = td
		self.ti = ti
		self.tr = tr
		self.kp = kp
		self.ki = ki 
		self.kd = kd 
		self.n = n
		self.beta = beta
		self.ts_fwd_ref = ts_fwd_ref

		self.i = 0.
		self.d = 0.

		self.y_old = 0.
		self.y_ref = 0.

		self.time = None

		self.setup()

		self.y_prev_t = self.time.timestamp()
		self.ref_prev_t = self.time.timestamp()

	def setup(self):
		self.use('calvinsys.native.python-time', shorthand='time')
		self.time = self['time']
		self.qt = self.time.timestamp()

	def did_migrate(self):
		self.setup()

	@condition(['y', 'y_ref'],['v'])
	def evaluate(self, yt, yt_ref):
		# Time management - for event based control
		self.y_ref, self.ref_prev_t = yt_ref
		y, t = yt
		dt = t-self.y_prev_t
		self.y_prev_t = t

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

		self.monitor_value = (v, self.y_ref)

		fwd_ts = self.ref_prev_t if self.ts_fwd_ref else self.y_prev_t 

		return ((v, fwd_ts), )

	action_priority = (evaluate,)
	requires = ['calvinsys.native.python-time']
