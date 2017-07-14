# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition

class PI_BnB(Actor):
    '''
    Super simple PI implementation for the Ball'n'Beam setup.
    
    Inputs:
        y: Measured value
        y_ref: Reference point
    Outputs:
        v: Control value
    '''

    @manage(['ti', 'tr', 'h', 'k', 'beta', 'i', 'v', 'e', 'time_prev_sample']) # 
    def init(self, ti=0., tr=1., h=.05, k=1., beta=1.): # Default parameter values from lab java code
        self.ti = ti
        self.tr = tr
        self.h = h
        self.k = k 
        self.beta = beta

        self.i = 0.
        self.v = 0.
        self.e = 0.

        self.time_prev_sample = 0.

        self.setup()

    def setup(self):
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']
        self.time_prev_sample = float(self.time.timestamp()) # Not a very appropriate value

    def did_migrate(self):
        self.setup()

    @condition(['y','y_ref'],['v'])
    def evaluate(self, y, y_ref):
        # Time management - for event based controll 
        # t = float(self.time.timestamp()) # ms?
        # dt = t-self.time_prev_sample/1000 
        # self.time_prev_sample = t

        y_ref = float(y_ref)
        y = float(y)

        # e
        self.e = y_ref - y

        # Control signal
        self.v = self.k * (self.beta * y_ref - y) + self.i

        # Update state
        #self.i += (self.k * dt / self.ti) * self.e * (dt / self.tr) * (float(input)-self.v)

        return (self.v, )

    @condition(['y_ref'],[])
    def set_ref(self, input):
        self.y_ref = float(input)

    action_priority = (evaluate, set_ref)
    requires = ['calvinsys.native.python-time']#, 'calvinsys.io.stdout']
