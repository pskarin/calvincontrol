# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition
import posix_ipc as ipc
import math
import sys

class SimWriter(Actor):

    """
    Writes to process simulation through a message queue

    Input:
      value : Input value & time
    """

    @manage(['device',])
    def init(self, device):
        self.device = device
        self.setup()

    def setup(self):
      self.outqueue = ipc.MessageQueue(self.device, flags=ipc.O_CREAT, max_messages=1)
      self.use('calvinsys.native.python-time', shorthand='time')
      self.time = self['time']

    # Can't actually migrate
    def will_migrate(self):
        self.outqueue.close()

    def did_migrate(self):
        self.setup()

    @condition(action_input=("value",))
    def write(self, value_ts):
        value, ts = value_ts
        try:
          self.outqueue.send("{}".format((value/10.0)*2*math.pi))
          self.monitor_value = self.time.timestamp()-ts
        except ipc.BusyError:
          sys.stderr.write("Failed to set new input, this should not happen\n")

    action_priority = (write, )
    requires = ['calvinsys.native.python-time']