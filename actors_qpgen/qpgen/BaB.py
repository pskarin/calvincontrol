# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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

_log = get_actor_logger(__name__)


class BaB(Actor):
  """
  Runs a simple MPC generated through QPgen

  Inputs:
    angle:    Beam angle
    position: Ball position
    ref:      Reference ball position in volts
  Outputs:
    u : Control signals
  """
  def init(self):
    self.qp = QP()
    self.prevpos = None
    self.prevtime = None
    self.Q = np.array(self.qp.getQ()).reshape((self.qp.numStates(), self.qp.numStates()))

  def did_migrate(self):
    pass

  @condition(action_input=['angle', 'position'], action_output=['u'])
  def action(self, angle_v, position_v):
    angle = (angle_v/10.0)*math.pi/4
    position = (position_v/10.0)*0.55
    speed = 0
    t = time.time()
    if self.prevpos != None:
      speed = (position-self.prevpos)/(t-self.prevtime)
    self.prevtime = t
    self.prevpos = position
    self.qp.setState((position, speed, angle))
    u0 = self.qp.run()
    u = (u0[0]/(2*math.pi))*10.0
#    print("{:6.2f} {:6.2f} {:6.2f} => {:6.2f} ({:6.2f})".format(angle,speed,position, u0[0], u))
    return (u,)

  @condition(action_input=['ref'], action_output=[])
  def setref(self, ref_v):
    r = np.array(((-ref_v/10.0)*0.55, 0, 0))
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

