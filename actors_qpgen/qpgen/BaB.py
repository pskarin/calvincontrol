# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#		 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from calvin.utilities.calvinlogger import get_actor_logger
from calvin.actor.actor import Actor, manage, condition

import numpy as np
from qpballnbeam import QP
import time
import math
import sys
from filterpy.kalman import update, predict

_log = get_actor_logger(__name__)


class BaB(Actor):
	"""
	Runs a simple MPC generated through QPgen
	Migrated attributes:
		ref_vt: Reference value in volts and time
		prevpos: The last measured ball state
		prevtime: Clock time from last measurement

	Inputs:
		angle:		Beam angle
		position: Ball position
		ref:			Reference ball position in volts
	Outputs:
		u : Control signals
		
	"""
	@manage(['ref_vt', 'prevpos', 'prevtime', 'u'])
	def init(self):
		self.ref_vt = (0,(0,))
		self.prevpos = 0
		self.prevtime = 0 # This will cause large denominator in first evaluation (speed)
		self.u = 0
		# Kalman filter matrices. Shall migrate.
		# TODO: Get sizes from QP!!!??
		self.P = np.eye(3)
		self.Q = np.eye(3)*np.array([1.1, 1.1, 0.1])
		self.R = np.eye(2)*np.array([1.1, 1.5])
		self.setup()

	def setup(self):
		self.qp = QP()
		self.qpQ = np.array(self.qp.getQ()).reshape((self.qp.numStates(), self.qp.numStates()))
		self.h = 1./self.qp.getSampleRate()
		self.F = np.array(self.qp.getA()).reshape(3,3)
		self.B = np.array(self.qp.getB())
		self.H = np.array([1., 0, 0, 0, 0, 1.]).reshape(2,3)
		self.x = np.array([0, 0, 0])
		sys.stderr.write("MPC N: {} h: {}\n".format(self.qp.horizon(), self.h))

	def did_migrate(self):
		self.setup()
		self.updateref()
		
	def volt2pos(self, v):
		return (v/10.0)*0.55

	def volt2angle(self, v):
		return (v/10.0)*math.pi/4
		
	def angular2volt(self, a):
		return (a/4.5)*10.0

	@condition(action_input=['angle', 'position', 'ref'], action_output=['u'])
	def action(self, angle_vt, position_vt, ref_vt):
		start_t = time.time()
		angle_v, angle_t, atick = angle_vt
		self.ref_vt = ref_vt[0:2]
		self.updateref()
		position_v, position_t, ptick = position_vt
		angle = self.volt2angle(angle_v)
		position = self.volt2pos(position_v)
		speed = (position-self.prevpos)/(position_t[0]-self.prevtime)

		self.x, self.P = predict(self.x, self.P, self.F, self.Q) 
		self.x, self.P = update(self.x, self.P, np.array([position, angle]), self.R, self.H, return_all=False)
		
		self.prevtime = position_t[0]
		self.prevpos = position
		self.qp.setState((self.x[0], self.x[1], self.x[2]))
		u0 = self.qp.run()
		iterations = self.qp.getNumberOfIterations()
		if iterations < 2000:
			self.u = self.angular2volt(u0[0])
		else:
			self.u = 0
		end_t = time.time()
		self.monitor_value = (self.u, iterations, end_t-start_t, speed)
#		sys.stderr.write("MPC Iterations: {} time: {}\n".format(iterations, round((end_t-start_t)*1000)))
		return ((self.u, (position_t+angle_t+self.ref_vt[1]), 0),)

	def updateref(self):
		r = np.array((self.volt2pos(self.ref_vt[0]), 0, 0))
		self.qp.setTargetStates(np.tile(np.dot(self.qpQ, r), (self.qp.horizon(),1)).reshape(
				self.qp.numStates()*self.qp.horizon(), 1))

	action_priority = (action,)

	def token_filter(port, token):
		if port == 'u':
			return map(lambda x: round(x, 2), token)
		return token

	# Double integrator sampled at 100Hz
	test_args = []

	test_set = [
		{
			'in': {'x': [[1,0], [0.9,0], [0.2, 0.1], [0,0]]},
			'out': {'u': [[-0.66], [-0.60], [-0.27], [0.0]]},
			'filter': token_filter
		},
	]

