# -*- coding: utf-8 -*-

from calvin.actor.actor import Actor, manage, condition, stateguard, calvinsys
import sys
from calvin.utilities.calvinlogger import get_actor_logger
_log = get_actor_logger(__name__)

class Clock(Actor):
    """ Hej
    
    Outputs:
        tick: tick count
    """
    @manage(['timer', 'period', 'started', 'tick', 'prev', 'next'])
    def init(self, period):
        _log.warning("Clock period: {}".format(period))
        self.period = period
        self.timer = calvinsys.open(self, "sys.timer.once")
        self.started = False
        self.tick = 0
        self.prev = 0
        self.next = 0
        self.setup()
  
    def setup(self):
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']

    def did_migrate(self):
        self.setup()

    @stateguard(lambda self: not self.started and calvinsys.can_write(self.timer))
    @condition([], ['tick'])
    def start_timer(self):
        self.started = True
        self.prev = self.time.timestamp()
        self.next = self.prev + self.period
        calvinsys.write(self.timer, self.period)
        return (self.tick, )

    @stateguard(lambda self: calvinsys.can_read(self.timer))
    @condition([], ['tick'])
    def trigger(self):
        calvinsys.read(self.timer)
        self.tick += 1
        t = self.time.timestamp()
        sys.stderr.write("Tick {:0.3f}\n".format(t-self.prev))
        self.prev = t
        while self.next < t: self.next += self.period
        calvinsys.write(self.timer, self.next-t)
        return (self.tick, )

    action_priority = (start_timer, trigger)
    requires = ['sys.timer.once', 'calvinsys.native.python-time']
