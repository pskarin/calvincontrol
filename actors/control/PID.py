# -*- coding: utf-8 -*-
import sys
from calvin.actor.actor import Actor, manage, condition, stateguard

class PID(Actor):
    """ Generic PID
    
    Inputs:
        y(routing="collect-single-slot"): Measured value
        y_ref(routing="collect-single-slot"): Reference point
    Outputs:
        v: Control value 
    """

    @manage(['td', 'ti', 'tr', 'kp', 'ki', 'kd', 'n' ,'beta', 'i', 'd', 'yt', 'y_old', 'yt_ref', 'y_prev_t', 'ref_prev_t', 'ts_fwd_ref', 'synched'])
    def init(self, td=1., ti=5., tr=10., kp=-.2, ki=0., kd=0., n=10., beta=1., ts_fwd_ref=False):
        self.td = td
        self.ti = ti
        self.tr = tr
        self.kp = kp
        self.ki = ki 
        self.kd = kd 
        self.n = n
        self.beta = beta
        self.ts_fwd_ref = ts_fwd_ref

        self.i = 0.
        self.d = 0.

        self.y_old = 0.
        self.yt = (0., 0, 0)
        self.yt_ref = (0., 0, 0)

        self.time = None
        self.synched = False
        self.setup()
        self.y_prev_t = self.time.timestamp()
        self.ref_prev_t = self.time.timestamp()

    def setup(self):
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']
        self.qt = self.time.timestamp()

    def did_migrate(self):
        self.setup()

    @stateguard(lambda self: not self.synched)
    @condition(['y'],[])
    def inputy(self, yt):
        self.yt = yt
        self.check_inputs()

    @stateguard(lambda self: not self.synched)
    @condition(['y_ref'],[])
    def inputyref(self, yt_ref):
        self.yt_ref = yt_ref
        self.check_inputs()

    def check_inputs(self):
        if self.yt[2] == self.yt_ref[2]:
            self.synched = True

    @stateguard(lambda self: self.synched)
    @condition([],['v'])
    def evaluate(self):
        # Time management - for event based control
        y_ref, self.ref_prev_t, tick = self.yt_ref
        y, t, _tick = self.yt
        dt = t-self.y_prev_t
        self.y_prev_t = t

        # 
        ad = self.td / (self.td + self.n*dt)
        bd = self.kd * ad * self.n

        # e
        e = y_ref - y

        # D
        self.d = ad*self.d - bd*(y - self.y_old)

        # Control signal
        v = self.kp * (self.beta * y_ref - y) + self.i + self.d

        # I
        self.i += (self.ki * dt/ self.ti) * e * (dt / self.tr) * (y-v)

        # Update state
        self.y_old = y

        self.monitor_value = (v, y_ref)

        fwd_ts = self.ref_prev_t if self.ts_fwd_ref else self.y_prev_t 

        self.synched = False
        return ((v, fwd_ts, tick), )

    action_priority = (inputy, inputyref, evaluate,)
    requires = ['calvinsys.native.python-time']
