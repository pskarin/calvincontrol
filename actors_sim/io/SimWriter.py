# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition
import posix_ipc as ipc
import math

class SimWriter(Actor):

    """
    Writes to process simulation through a message queue

    Input:
      value : Input value
    """

    @manage(['device',])
    def init(self, device):
        self.device = device
        self.setup()

    def setup(self):
      self.outqueue = ipc.MessageQueue(self.device, flags=ipc.O_CREAT, max_messages=1)

    # Can't actually migrate
    def will_migrate(self):
        self.outqueue.close()

    def did_migrate(self):
        self.setup()

    @condition(action_input=("value",))
    def write(self, value):
        try:
          self.outqueue.send("{}".format((value/10.0)*2*math.pi))
	  self.monitor_value = value
        except ipc.BusyError:
          print("Failed to set new input, this should not happen")

    action_priority = (write, )
