# -*- coding: utf-8 -*-

from calvin.actor.actor import Actor, manage, condition, stateguard, calvinsys

class PacedValueIterator(Actor):
    """ Sequentially pass a value from __values__ at __tick__
    
    Inputs:
        tick: Clock tick
    Outputs:
        value: a value from __values__
    """

    @manage(['period', 'values', 'index'])
    def init(self, period, values):
        self.period = period
        self.values = values
        # Add exception for len(values) <= 2
        self.index = 0 
        self.timer = None
        self.setup()

    def setup(self):
        self.use('calvinsys.events.timer', shorthand='timer')
        self.use('calvinsys.native.python-time', shorthand='time')
        self.start()

    def start(self):
        self.timer = self['timer'].repeat(self.period)

    def will_migrate(self):
        if self.timer:
            self.timer.cancel()

    def did_migrate(self):
        self.setup()

    @condition(['tick'], ['value'])
    def clocktick(self, tick):
        value = self.values[self.index]
        self.monitor_value = value
        return ((value, self['time'].timestamp(), tick),)
    
    @stateguard(lambda self: self.timer and self.timer.triggered)
    @condition([], [])
    def trigger(self):
        self.timer.ack()
        self.index =  (self.index + 1)%len(self.values)

    action_priority = (clocktick, trigger)
    requires = ['calvinsys.events.timer','calvinsys.native.python-time']
