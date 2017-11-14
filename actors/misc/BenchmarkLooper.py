# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition, stateguard

class BenchmarkLooper(Actor):
	"""
	Sequentially pass a value from __values__ at __tick__
	Inputs: 
		token: A trigger. 
	Outputs:
		out: default value
		dt: delta t  
	"""

	@manage(['delay', 'default', 'started'])
	def init(self, delay, default):
		self.delay = delay
		self.default = default

		self.timer = None
		self.started = False
		self.prev_time = None
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
	@condition([], ['out'])
	def trigger(self):
		self.timer.ack()
		self.prev_time = self['time'].timestamp()
		return (self.default, )

	@condition(['token'], ['out', 'dt'])
	def through(self, token):
		t_now = self['time'].timestamp()
		dt = t_now - self.prev_time
		self.prev_time = t_now
		return (self.default, dt )

	action_priority = (start_timer, trigger, through)
	requires = ['calvinsys.events.timer', 'calvinsys.native.python-time']
