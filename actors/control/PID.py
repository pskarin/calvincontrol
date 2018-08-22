# -*- coding: utf-8 -*-
import sys
from calvin.actor.actor import Actor, manage, condition, stateguard, calvinsys

from calvin.utilities.calvinlogger import get_actor_logger
_log = get_actor_logger(__name__)

class PID(Actor):
	'''
	Generic PID
	
	Inputs:
		y: Measured value
		y_ref: Reference point
	Outputs:
		v: Control value 
	'''

	@manage(['td', 'ti', 'tr', 'kp', 'ki', 'kd', 'n' ,'beta', 'i', 'd', 'y_old', 'y_prev_t'])
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

		self.time = None
		self.setup()
		self.y_prev_t = self.time.timestamp()
    
		self.yta = []
		self.yt_refa = []

	def setup(self):
		self.use('calvinsys.native.python-time', shorthand='time')
		self.time = self['time']
		self.qt = self.time.timestamp()

	def did_migrate(self):
		self.setup()

#	def pre_condition_wrapper(self):
#		""" NOTE! The algorithm at this point assumes that there are only two queues! """
#		isready = True
#		keys = self.inports.keys()
#		discarded = {}
#		for k in keys: discarded[k] = 0    
#		for xk,xv in self.inports.iteritems():
#			if xv.num_tokens() > 0:
#				top = xv.get_token_from_top(0).value
#				for yk in [k for k in keys if not k == xk]:
#					yv = self.inports[yk]
#					cont = True
#					while yv.num_tokens() > 1 and cont:
#						yt0 = yv.get_token_from_top(0).value
#						yt1 = yv.get_token_from_top(1).value
#						if abs(yt0[1]-top[1]) > abs(yt1[1]-top[1]):
#							yv.read()
#							discarded[yk] += 1
#						else:
#							cont = False
#			else:
#				isready = False # Some queue is empty
#		if isready:
#			mintokens = min([x.num_tokens() for x in self.inports.values()])
#			for xk in keys:
#				xv = self.inports[xk]
#				for r in range(0, mintokens-1):
#					xv.read()
#					discarded[xk] += 1
#				self.log_queue_precond(xk, discarded[xk], xv.get_token_from_top(0).value[1])

	@condition(['y', 'y_ref'],['v'])
	def cal_output(self, yt, yt_ref):
		# Time management - for event based control
		y_ref, ref_t, tick = yt_ref
		y, y_t, _tick = yt
		dt = y_t[0]-self.y_prev_t
		self.y_prev_t = y_t[0]

		# 
		ad = self.td / (self.td + self.n*dt)
		bd = self.kd * ad * self.n

		# e
		e = y_ref - y

		# D
		self.d = ad*self.d - bd*(y - self.y_old)

		# Control signal
		v = self.kp * (self.beta * y_ref - y) + self.i + self.d

		# I
		self.i += (self.ki * dt/ self.ti) * e * (dt / self.tr) * (y-v)

		# Update state
		self.y_old = y

		self.monitor_value = v

		return ((v, y_t + ref_t, tick), )

	action_priority = (cal_output,)
	requires = ['calvinsys.native.python-time']
