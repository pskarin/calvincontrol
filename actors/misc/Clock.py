# -*- coding: utf-8 -*-

from calvin.actor.actor import Actor, manage, condition, stateguard, calvinsys

class Clock(Actor):
    """ Hej
    
    Outputs:
        tick: tick count
    """
    @manage(['timer', 'period', 'started', 'tick'])
    def init(self, period):
        self.period = period
        self.timer = calvinsys.open(self, "sys.timer.repeating")
        self.started = False
        self.tick = 0

    @stateguard(lambda self: not self.started and calvinsys.can_write(self.timer))
    @condition([], ['tick'])
    def start_timer(self):
        self.started = True
        calvinsys.write(self.timer, self.period)
        return (self.tick, )

    @stateguard(lambda self: calvinsys.can_read(self.timer))
    @condition([], ['tick'])
    def trigger(self):
        calvinsys.read(self.timer)
        self.tick += 1
        return (self.tick, )

    action_priority = (start_timer, trigger)
    requires = ['sys.timer.repeating']
