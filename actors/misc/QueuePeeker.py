# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition, stateguard

class QueuePeeker(Actor):
	"""
	Sequentially pass a value from __values__ at __tick__
	Inputs: 
		token: A trigger. 
	Outputs:
		out: default value
		dt: delta t  
	"""

	@manage(['delay', 'started'])
	def init(self, delay):
		self.delay = delay

		self.timer = None
		self.started = False
		self.setup()

	def setup(self):
		self.use('calvinsys.events.timer', shorthand='timer')

	def start(self):
		self.timer = self['timer'].once(self.delay)
		self.started = True

	def will_migrate(self):
		if self.timer:
			self.timer.cancel()

	def did_migrate(self):
		self.setup()
		if self.started:
			self.start()

	@stateguard(lambda self: not self.started)
	@condition([], [])
	def start_timer(self):
		self.start()

	@stateguard(lambda self: self.timer and self.timer.triggered)
	@condition([], ['out'])
	def trigger(self):
        if self.inports:
            for p in self.inports.values():
                print p

	action_priority = (start_timer, trigger)
	requires = ['calvinsys.events.timer']
