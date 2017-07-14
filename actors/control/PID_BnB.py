# -*- coding: utf-8 -*-

# William Tärneberg 2017
from calvin.actor.actor import Actor, manage, condition

class PID_BnB(Actor):
    '''
    Super simple PID implementation for the Ball'n'Beam setup.
    
    Inputs:
        y: Measured value
        y_ref: Reference point
    Outputs:
        v: Control value
    '''

    @manage(['td', 'ti', 'tr', 'h', 'k', 'n' ,'beta', 'i', 'd', 'v', 'e', 'y', 'y_old', 'ad', 'bd', 'time_prev_sample', 'y_ref']) # 
    def init(self, td=1., ti=5., tr=10., h=.05, k=-.2, n=10., beta=1.):
        self.td = td
        self.ti = ti
        self.tr = tr
        self.h = h
        self.k = k 
        self.n = n
        self.beta = beta

        self.i = 0.
        self.d = 0.
        self.v = 0.
        self.e = 0.
        self.y = 0.
        self.y_old = 0.
        self.y_ref = 0.

        self.time_prev_sample = 0.
        self.bd = 0.
        self.ad = 0.

        self.setup()

    def setup(self):
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']
        self.time_prev_sample = float(self.time.timestamp()) # Not a very appropriate value

    def did_migrate(self):
        self.setup()

    @condition(['y'],['v'])
    def evaluate(self, input):
        # Time management - for event based controll 
        t = float(self.time.timestamp()) # ms?
        dt = t-self.time_prev_sample
        self.time_prev_sample = t

        # Input 
        self.y = float(input)

        # 
        self.ad = self.td / (self.td + self.n*dt)
        self.bd = self.k * self.ad * self.n

        # e
        self.e = self.y_ref - self.y

        # D
        self.d = self.ad*self.d - self.bd*(self.y - self.y_old)

        # Control signal
        self.v = self.k * (self.beta * self.y_ref - self.y) + self.i + self.d

        # Update state
        self.y_old = self.y
        #self.i += (self.k * self.h / self.ti) * self.e * (self.h / self.tr) * (float(input)-self.v)

        return (self.v, )

    @condition(['y_ref'],[])
    def set_ref(self, input):
        self.y_ref = float(input)

    action_priority = (evaluate, set_ref)
    requires = ['calvinsys.native.python-time']#, 'calvinsys.io.stdout']
