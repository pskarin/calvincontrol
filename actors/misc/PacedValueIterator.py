# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition, stateguard

class PacedValueIterator(Actor):
    """
    Sequentially pass a value from __values__ at __tick__
    Outputs:
        value: a value from __values__
    """

    @manage(['tick', 'values', 'index', 'started'])
    def init(self, tick, values):
        self.tick = tick
        self.values = values
        # Add exception for len(values) <= 2
        self.index = 0 
        self.timer = None
        self.started = False
        self.setup()

    def setup(self):
        self.use('calvinsys.events.timer', shorthand='timer')

    def start(self):
        self.timer = self['timer'].repeat(self.tick)
        self.started = True

    def will_migrate(self):
        if self.timer:
            self.timer.cancel()

    def did_migrate(self):
        self.setup()
        if self.started:
            self.start()

    @stateguard(lambda self: not self.started)
    @condition([], ['value'])
    def start_timer(self):
        self.start()

        value = self.values[self.index]
        self.index =  (self.index + 1)%len(self.values)

	self.monitor_value = value

        return (value, )

    @stateguard(lambda self: self.timer and self.timer.triggered)
    @condition([], ['value'])
    def trigger(self):
        self.timer.ack()
        value = self.values[self.index]
        self.index =  (self.index + 1)%len(self.values)

	self.monitor_value = value

        return (value, )

    action_priority = (start_timer, trigger)
    requires = ['calvinsys.events.timer']
