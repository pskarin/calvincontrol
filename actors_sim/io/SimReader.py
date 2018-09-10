# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition, stateguard
import posix_ipc as ipc
import numpy as np
import sys

from calvin.utilities.calvinlogger import get_actor_logger
_log = get_actor_logger(__name__)

class SimReader(Actor):

	"""
	Reads process simulation from a message queue

	Inputs:
	    tick: Clock tick
        Outputs:
	    value: Output value
	"""

	@manage(['device', 'value', 'scale', 'noise'])#, 'del_q', 'max_q'])
        def init(self, device, scale, noise=0., mean=0.):#, max_q=1000):
                _log.warning("SimReader; Setting up")
                self.device = device
		self.value = 0
		self.scale = scale
		self.noise = noise
		self.mean = mean
                #self.del_q = deque([], maxlen=self.max_q)
		self.setup()
                _log.warning("SimReader; Finished")

	def setup(self):
		self.inqueue = ipc.MessageQueue(self.device, flags=ipc.O_CREAT, max_messages=1)
		self.use('calvinsys.native.python-time', shorthand='time')
		self.time = self['time']

	def will_migrate(self):
		self.inqueue.close()

	# Can't actually migrate
	def did_migrate(self):
		self.setup()

	def read(self):
		try:        
			message, priority = self.inqueue.receive(0) # Get input signal
			self.value = float(message)/self.scale*10.0
			if self.noise > 0: self.value += np.random.normal(self.mean, self.noise, 1)[0]
			self.value = max(-10.0, min(10.0, self.value))
		except ipc.BusyError:
			pass
		return self.value

	@condition(['tick'], ['value'])
	def trigger(self, tick):
		value = self.read()
		self.monitor_value = value
                _log.info("ADC Reader: Value sent out.")
		return ((value, (self.time.timestamp(),), tick),)

	action_priority = (trigger,  )
	requires = ['calvinsys.native.python-time']
