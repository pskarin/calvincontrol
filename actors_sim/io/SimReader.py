# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition, stateguard
import posix_ipc as ipc
import numpy as np
import os
import os.path
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

	@manage(['device', 'value', 'scale', 'noise', 'log_data', 'log_file', 'log_maxsize'])
        def init(self, device, scale, noise=0., mean=0., log_data=False, log_file="/tmp/tmp_log.txt", log_maxsize=10**6):
                _log.warning("SimReader; Setting up")
                self.device = device
		self.value = 0
		self.scale = scale
		self.noise = noise
		self.mean = mean

                self.log_data = log_data
                self.log_file = log_file
                self.log_maxsize = log_maxsize

		self.setup()
                _log.warning("SimReader; Finished")

	def setup(self):
		self.inqueue = ipc.MessageQueue(self.device, flags=ipc.O_CREAT, max_messages=1)
		self.use('calvinsys.native.python-time', shorthand='time')
		self.time = self['time']
                if self.log_data:
                    with open(self.log_file, 'w') as f:
                        f.write("\n")

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
		t = self.time.timestamp()

                self.monitor_value = value
                _log.info("ADC Reader: Value sent out.")

                if self.log_data and os.stat(self.log_file).st_size < self.log_maxsize:
                    with open(self.log_file, 'a') as f:
                        f.write("{},{},{}\n".format(value, t, tick))
		
                return ((value, (t,tick, None,), None,),)

	action_priority = (trigger,  )
	requires = ['calvinsys.native.python-time']
