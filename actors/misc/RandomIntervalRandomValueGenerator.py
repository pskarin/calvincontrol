# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition, stateguard

import random as rnd

class RandomIntervalRandomValueGenerator(Actor):
    """
    Sequentially pass a value from __values__ at __tick__
    Outputs:
        value: a value from __values__
    """

    @manage(['tick_range', 'value_range', 'index', 'started'])
    def init(self, tick_range, value_range):
        self.tick_range = tick_range
        self.value_range = value_range
        self.index = 0 
        self.timer = None
        self.started = False
        self.setup()

    def setup(self):
        self.use('calvinsys.events.timer', shorthand='timer')

    def start(self):
        self.timer = self['timer'].once( rnd.uniform( self.tick_range[0], self.tick_range[1]))
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

        value = 0
        
        return (value, )

    @stateguard(lambda self: self.timer and self.timer.triggered)
    @condition([], ['value'])
    def trigger(self):
        self.timer.ack()
        value = rnd.randint( self.value_range[0], self.value_range[1])

        self.start()

        return (value, )

    action_priority = (start_timer, trigger)
    requires = ['calvinsys.events.timer','calvinsys.native.python-time']
