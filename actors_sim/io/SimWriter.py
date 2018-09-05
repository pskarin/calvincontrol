# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition
import posix_ipc as ipc
import math
import sys
from calvin.utilities.calvinlogger import get_actor_logger
_log = get_actor_logger(__name__)

class SimWriter(Actor):

    """
    Writes to process simulation through a message queue

    Inputs:
        value : Input value & time
    Outputs:
        delay_inner: Output the measured delay for inner controller 
        delay_outer: Output the measured delay for outer controller
    """

    @manage(['device', 'delay_inner', 'delay_outer', 'inner_trig', 'outer_trig'])
    def init(self, device):
        _log.warning("SimWriter; Setting up")
        self.device = device
        self.setup()
        _log.warning("SimWriter; Finished")

    def setup(self):
      self.outqueue = ipc.MessageQueue(self.device, flags=ipc.O_CREAT, max_messages=1)
      self.use('calvinsys.native.python-time', shorthand='time')
      self.time = self['time']

    # Can't actually migrate
    def will_migrate(self):
        self.outqueue.close()

    def did_migrate(self):
        self.setup()

    @condition(["value"], ["delay_inner", "delay_outer"])
    def write(self, value_ts):
        _log.warning("Triggering write")
        value, t1, t2 = value_ts
        ts, tick = t1

        try:
            self.outqueue.send("{}".format((value/10.0)*2*math.pi))
            myts = self.time.timestamp()
            diffs = []
            for t in ts:
                diffs.append(myts-t)
            self.monitor_value = diffs
        except ipc.BusyError:
            sys.stderr.write("Failed to set new input, this should not happen\n")
        finally: 
            delay_inner = (self.time.timestamp() - t1[0], t1[1])
            delay_outer = (self.time.timestamp() - t2[0], t2[1])
            return (delay_inner, delay_outer, )

    action_priority = (write, )
    requires = ['calvinsys.native.python-time']
