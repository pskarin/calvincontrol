# -*- coding: utf-8 -*-
from calvin.actor.actor import Actor, manage, condition, stateguard
import posix_ipc as ipc

class SimReader(Actor):

    """
    Reads process simulation from a message queue
    Outputs:
      value: Output value
    """

    @manage(['tick', 'device', 'timer', 'started', 'value', 'scale'])
    def init(self, tick, device, scale):
        self.tick = tick
        self.device = device
        self.value = 0
        self.scale = scale

        self.timer = None 
        self.started = False 

        self.setup()

    def setup(self):
        self.use('calvinsys.events.timer', shorthand='timer')
        self.inqueue = ipc.MessageQueue(self.device, flags=ipc.O_CREAT, max_messages=1)

    def start(self):
        self.timer = self['timer'].repeat(self.tick)
        self.started = True

    def will_migrate(self):
        self.inqueue.close()
        if self.timer:
            self.timer.cancel()

    # Can't actually migrate
    def did_migrate(self):
        self.setup()
        if self.started:
            self.start()

    def read(self):
      try:        
        message, priority = self.inqueue.receive(0) # Get input signal
        self.value = max(-10.0, min(10.0, float(message)/self.scale*10.0))
      except ipc.BusyError:
        pass
      return self.value

    @stateguard(lambda self: not self.started)
    @condition([], ['value'])
    def start_timer(self):
        value = self.read()
        self.start()

	self.monitor_value = value

        return (value, )

    @stateguard(lambda self: self.timer and self.timer.triggered)
    @condition([], ['value'])
    def trigger(self):
        self.timer.ack()

	value = self.read()

	self.monitor_value = value 

        return (value, )

    action_priority = (start_timer, trigger)
    requires = ['calvinsys.events.timer']
