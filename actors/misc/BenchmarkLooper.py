# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition, stateguard

class BenchmarkLooper(Actor):
	"""
	Sequentially pass a value from __values__ at __tick__
	Inputs: 
		token: 
	Outputs:
		token: a value from __values__
	"""

	@manage(['delay', 'default', 'started'])
	def init(self, delay, default):
		self.delay = delay
		self.default = default

		self.timer = None
		self.started = False
		self.setup()

	def setup(self):
		self.use('calvinsys.events.timer', shorthand='timer')
		self.use('calvinsys.native.python-time', shorthand='time')

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
	@condition([], ['token'])
	def trigger(self):
		self.timer.ack()
		return (self.default, )

	@condition(['token'], ['token'])
	def passthrough(self, token):
		print self['time'].timestamp()
		return (token, )

	action_priority = (start_timer, trigger, passthrough)
	requires = ['calvinsys.events.timer', 'calvinsys.native.python-time']
