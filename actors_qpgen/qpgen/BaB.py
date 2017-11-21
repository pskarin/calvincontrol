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

_log = get_actor_logger(__name__)


class BaB(Actor):
	"""
	Runs a simple MPC generated through QPgen
	Migrated attributes:
		ref_v	: Reference value in volts
		prevpos: The last measured ball state
		prevtime: Clock time from last measurement

	Inputs:
		angle:		Beam angle
		position: Ball position
		ref:			Reference ball position in volts
	Outputs:
		u : Control signals
		
	"""
	@manage(['ref_v', 'prevpos', 'prevtime', 'u'])
	def init(self):
		self.ref_v = 0
		self.prevpos = 0
		self.prevtime = 0 # This will cause large denominator in first evaluation (speed)
		self.u = 0
		self.setup()

	def setup(self):
		self.qp = QP()
		self.Q = np.array(self.qp.getQ()).reshape((self.qp.numStates(), self.qp.numStates()))
		self.h = 1./self.qp.getSampleRate()

	def did_migrate(self):
		self.setup()
		self.updateref()
		
	@condition(action_input=['angle', 'position'], action_output=['u'])
	def action(self, angle_vt, position_vt):
		t = time.time()
		angle_v, angle_t = angle_vt
		position_v, position_t = position_vt
		angle = (angle_v/10.0)*math.pi/4
		position = (position_v/10.0)*0.55
		speed = (position-self.prevpos)/self.h
		self.prevtime = position_t
		self.prevpos = position
		self.qp.setState((position, speed, angle))
		u0 = self.qp.run()
		iterations = self.qp.getNumberOfIterations()
		if iterations < 2000:
			self.u = (u0[0]/(2*math.pi))*10.0
		sys.stderr.write("a:{:6.2f} s:{:6.2f} p:{:6.2f} => w:{:6.2f} v:({:6.2f}) t:{:6.3f} i:{}\n".format(
			angle,speed,position, u0[0], self.u, time.time()-t, iterations))
		return (self.u,)

	@condition(action_input=['ref'], action_output=[])
	def setref(self, ref_v):
		self.ref_v = ref_v
		self.updateref()

	def updateref(self):
		r = np.array(((-self.ref_v/10.0)*0.55, 0, 0))
		self.qp.setTargetStates(np.tile(np.dot(self.Q, r), (self.qp.horizon(),1)).reshape(
				self.qp.numStates()*self.qp.horizon(), 1))

	action_priority = (action, setref)

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

