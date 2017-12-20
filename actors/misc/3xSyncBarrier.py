# -*- coding: utf-8 -*-

# William Tärneberg 2017

from calvin.actor.actor import Actor, manage, condition

class 3xSyncBarrier(Actor):
	"""
	Pass input after a given delay
	Input :
		in1(routing="collect-single-slot"): token 1 
		in2(routing="collect-single-slot"): token 2  
		in3(routing="collect-single-slot"): token 3  
	Outputs:
		out1 : token 1 
		out2 : token 2 
		out3 : token 3 
	"""

	@manage(['prev_sync_time'])
	def init(self):
		self.prev_sync_time = None

		self.setup()

	def did_migrate(self):
        self.setup()

	def setup(self):
		self.use('calvinsys.native.python-time', shorthand='time')
		self.prev_sync_time = self['time'].timestamp()

	@condition(['in1','in2','in3'], ['out1','out2','out3'])
	def push(self, in1, in2, in3):
		
		time_now = self['time'].timestamp()

		self.monitor_value = time_now - self.prev_sync_time

		self.prev_sync_time = time_now

		return (in1, in2, in3, )

	action_priority = (push,)
	requires = ['calvinsys.native.python-time']
