# -*- coding: utf-8 -*-

from calvin.actor.actor import Actor, manage, condition, stateguard
import os

from calvin.utilities.calvinlogger import get_actor_logger
_log = get_actor_logger(__name__)

class PacedValueIterator(Actor):
	"""
	Sequentially pass a value from __values__ at __tick__
	Inputs:
		tick: Clock tick
	Outputs:
		value: a value from __values__
	"""

	@manage(['period', 'values', 'index', 'log_data', 'log_file', 'log_maxsize'])
	def init(self, period, values, log_data=False, log_file="/tmp/log_ref.txt", log_maxsize=10**6):
		self.period = period
		self.values = values
		# Add exception for len(values) <= 2
		self.index = 0 
		self.timer = None

                self.log_data = log_data
                self.log_file = log_file
                self.log_maxsize = log_maxsize
                
		self.setup()
                
                _log.warning("Paced Iterator; Finished")

	def setup(self):
		self.use('calvinsys.events.timer', shorthand='timer')
		self.use('calvinsys.native.python-time', shorthand='time')
		self.start()
                
                if self.log_data:
                    with open(self.log_file, 'w') as f:
                        f.write("\n")

	def start(self):
		self.timer = self['timer'].repeat(self.period)

	def will_migrate(self):
		if self.timer:
			self.timer.cancel()

	def did_migrate(self):
		self.setup()

	@condition(['tick'], ['value'])
	def clocktick(self, tick):
                _log.warning("Paced Iterator; Triggered")
		value = self.values[self.index]
		self.monitor_value = value
               
                t = self['time'].timestamp()
                _log.warning("Paced Iterator; Time retrieved")

                if self.log_data and os.stat(self.log_file).st_size < self.log_maxsize:
                    with open(self.log_file, 'a') as f:
                        f.write("{},{},{}\n".format(value, t, tick))
                
                _log.warning("Paced Iterator; Output logged")
		
                return ((value, (t, tick, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0, 0.0)),)
    
	@stateguard(lambda self: self.timer and self.timer.triggered)
	@condition([], [])
	def trigger(self):
		self.timer.ack()
		self.index =  (self.index + 1)%len(self.values)

	action_priority = (clocktick, trigger)
	requires = ['calvinsys.events.timer','calvinsys.native.python-time']
