# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition
import posix_ipc as ipc
import math
import os
import os.path
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

    @manage(['device', 'output_filename', 'log_data', 'log_maxsize'])
    def init(self, device, log_data=False, log_maxsize=10**6):
        _log.warning("SimWriter; Setting up")
        self.device = device
        self.log_data = log_data
        self.log_maxsize = log_maxsize 
        self.output_filename = "/tmp/log_writer.txt"
        self.setup()
        _log.warning("SimWriter; Finished")

    def setup(self):
        self.outqueue = ipc.MessageQueue(self.device, flags=ipc.O_CREAT, max_messages=1)
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']
        if self.log_data:
            with open(self.output_filename, 'w') as f:
                f.write("\n")

    # Can't actually migrate
    def will_migrate(self):
        self.outqueue.close()

    def did_migrate(self):
        self.setup()

    @condition(["value"], ["delay_inner", "delay_outer"])
    def write(self, value_ts):
        _log.warning("Triggering write")
        value, t1, t2 = value_ts
        ts, tick, _, _, _ = t1
        _log.info("Actuator: time for passing the delay actor: {}".format(self.time.timestamp() - ts))
        try:
            _log.warning("value: {}".format(value))
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

            de_inner = t1[2] - delay_inner[0]
            de_outer = t2[2] - delay_outer[0]
            
            _log.warning("Inner; delay error {}, Estimated delay {}, actual delay {}"\
                    .format(de_inner, t1[2], delay_inner[0])) 
            _log.warning("Outer; delay error {}, Estimated delay {}, actual delay {}"\
                    .format(de_outer, t2[2], delay_outer[0])) 
           
            if self.log_data and os.stat(self.output_filename).st_size < self.log_maxsize:
                with open(self.output_filename, 'a') as f:
                    f.write("{},{},{},{},{},{},{},{}\n".format(t1[2], delay_inner[0], t2[2], delay_outer[0], t1[3], t1[4], t2[3], t2[4]))

            _log.warning("Got here")
            return (delay_inner, delay_outer, )

    action_priority = (write, )
    requires = ['calvinsys.native.python-time']
