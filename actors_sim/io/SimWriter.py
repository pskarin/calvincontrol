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

    Input:
        value : Input value & time
    Output:
        delay_inner: Output the measured delay for inner controller 
        delay_outer: Output the measured delay for outer controller
    """

    @manage(['device', 'delay_inner', 'delay_outer', 'inner_trig', 'outer_trig'])
    def init(self, device):
        _log.warning("SimWriter; Setting up")
        self.device = device
        self.delay_inner = (0.0, 0.0)
        self.delay_outer = (0.0, 0.0)
        self.inner_trig = False
        self.outer_trig = False
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

    @stateguard(lambda self: (self.inner_trig))
    @condition([], ["delay_inner"])    
    def send_delay_inner(self):
        self.inner_trig = False
        return (self.delay_inner, )
    
    @stateguard(lambda self: (self.outer_trig))
    @condition([], ["delay_outer"])    
    def send_delay_outer(self):
        self.outer_trig = False
        return (self.delay_outer, )

    @condition(["value"], [])
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
            self.delay_inner = (time.timestamp() - t1[0], t1[1])
            self.delay_outer = (time.timestamp() - t2[0], t2[1])
            self.inner_trig = True
            self.outer_trig = True
            return

    action_priority = (write, send_delay_inner, send_delay_outer, )
    requires = ['calvinsys.native.python-time']
