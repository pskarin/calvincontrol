# -*- coding: utf-8 -*-
import sys
from calvin.actor.actor import Actor, manage, condition, stateguard, calvinsys
from calvin.utilities.calvinlogger import get_actor_logger
from collections import deque
import os
import os.path
import numpy as np
_log = get_actor_logger(__name__)


class APIDSmith(Actor):
    '''
    PID controller with asynchronous updates. Uses the Smith predictor to compensate for delays.
    The model of the process needs to be supplied in this script.

    Inputs:
        y: Measured value
        y_ref: Reference point
        measured_delay: The measured true delay
        u_d: Smith delay input
    Outputs:
        v: Control value
        u_d: Smith delay trigger
    '''

    @manage(['td', 'ti', 'tr', 'kp', 'ki', 'kd', 'n', 'beta', 'i', 'd',
             'y_old', 't_old', 't_old_meas', 'timer', 'period', 'started', 
             'tick', 'y_estim', 'y_ref', 'name', 'delay_tick', 'delay_est',
             'estimate', 'log_data', 'log_maxsize', 'log_file', 'E_1', 'E_2',
             'tick_smith', 't_old_smith'])
    def init(self, td=1., ti=5., tr=10., kp=-.2, ki=0., kd=0., n=10.,
                beta=1., period=0.05, max_q=1000, aname="Name", estimate=0,
                log_data=0, log_file="/tmp/pid_tmp_log.txt", log_maxsize=10**6):
        _log.warning("PID Clock period: {}".format(period))
        self.td = td
        self.ti = ti
        self.tr = tr
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.n = n
        self.beta = beta
        self.period = period
        self.max_q = max_q
        self.i = 0.
        self.d = 0.
        self.name = aname
        self.delay_tick = 0
        self.delay_est = 0

        self.estimate = estimate

        self.y_old = 0.
        self.E_1 = 0.0
        self.E_2 = 0.0
        self.model = lambda x, u: x + 4.5*u 
        self.tick_smith = 0

        self.log_data = log_data
        self.log_maxsize = log_maxsize 
        self.log_file = log_file

        self.started = False
        self.tick = 0
        self.setup()
        self.t_old = self.time.timestamp()
        self.t_old_meas = self.time.timestamp()
        self.t_old_smith = self.time.timestamp()
        self.y_estim = (0, 0)
        self.y_ref = (0, (self.t_old_meas, self.tick, 1.0), (0.0, 0.0, 0.0))
        
        # Message queue (deque is thread-safe no need for a lock)
        #self.msg_q = deque([], maxlen=self.max_q)
        # Estimator
        #self.msg_estim_q = deque([], maxlen=self.max_q)

    def setup(self):
        self.timer = calvinsys.open(self, "sys.timer.once")
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']
        self.qt = self.time.timestamp()
        _log.warning("Set up")
        Cont = calvinsys.can_write(self.timer)
        
        if self.log_data:
            with open(self.log_file, 'w') as f:
                f.write("\n")

        if not Cont:
            _log.warning("  Can't write timer")
        elif not self.started:
            _log.warning("  write timer")
        


    #@stateguard(lambda self: (not self.started and calvinsys.can_write(self.timer)))
    #@condition([], [])
    def start_timer(self, period):
        _log.info("{}: Start Timer with period: {}".format(self.name, period))
        if not calvinsys.can_write(self.timer):
            calvinsys.read(self.timer)
            calvinsys.close(self.timer)
        self.started = True
        calvinsys.write(self.timer, period)
        return

    @stateguard(lambda self: calvinsys.can_read(self.timer))
    @condition([], ['v', 'u_d'])
    def timer_trigger(self):
        _log.warning(self.name + "; Tick: {}".format(self.tick))
        _log.debug('Take values from buffer on timer trigger.')
        calvinsys.read(self.timer)
        self.tick += 1

        v = self.calc_output()
        _log.warning(self.name + "; calculation complete, returning and start timer for next period")
        self.start_timer(self.period)
       
        # TODO: Add correct waiting term!
        u_d = (v[0], self.delay_est + (self.time.timestamp() - self.t_old_meas), v[1][1])
        return (v, u_d,)

    @condition(['u_d'], [])
    def update_smith(self, u_d):
        _log.warning("Update smith")
        if self.tick_smith < u_d[2]:
            self.tick_smith = u_d[2]

            t = self.time.timestamp()
            dt = t - self.t_old_smith
            self.t_old_smith = t

            self.E_2 = self.model(self.E_2, dt*u_d[0])
        

    #@stateguard(lambda self: (calvinsys.can_read(self.y)))
    @condition(['y'], [])
    def msg_trigger(self, y):
        if not self.estimate:
            self.y_estim = (y[0], y[1][0])
        else:
            self.y_estim = (y[0] + self.E_1 - self.E_2, self.time.timestamp()) #y[1][0] + self.delay_est)
            self.t_old_meas = y[1][0]

        if self.log_data and os.stat(self.log_file).st_size < self.log_maxsize:
            with open(self.log_file, 'a') as f:
                f.write("{},{},{},{}\n".format(self.y_estim[0], self.E_1, self.E_2, self.y_estim[1]))

        _log.info("{}: trigger the controller for the new arrival token.".format(self.name))
        self.start_timer(0)
        return

    @condition(['y_ref'], [])
    def ref_trigger(self, y_ref):
        _log.warning(self.name + "; updating reference: {}".format(y_ref))
        if self.y_ref[1][0] < y_ref[1][0]: # Only update when new reference is more fresh
            self.y_ref = y_ref
        return

    @condition(['measured_delay'], [])
    def delay_trigger(self, measured_delay):
        if measured_delay[1] > self.delay_tick:
            # Estimate delay using a simple EWMA filter
            self.delay_est = 0.2*measured_delay[0] + 0.8*self.delay_est
            self.delay_tick = measured_delay[1]
        else:
            _log.warning("Sent delay is behind current estimate")

        _log.warning("Est delay: {}, old delay: {}".format(self.delay_est, measured_delay[0]))
        return

    def did_migrate(self):
        self.setup()
    
    def calc_output(self):
        y_ref, t_ref, _  = self.y_ref
        y = self.y_estim[0]
        t = self.time.timestamp()
        dt = t - self.t_old
        self.t_old = t

        #
        ad = self.td / (self.td + self.n * dt)
        bd = self.kd * ad * self.n

        # e
        e = y_ref - y

        # D
        self.d = ad * self.d - bd * (y - self.y_old)

        # Control signal
        u = self.kp * (self.beta * y_ref - y) + self.i + self.d

        # I
        self.i += (self.ki * dt / self.ti) * e * (dt / self.tr) * (y - u)

        # Update state
        self.y_old = y
        
        self.monitor_value = u
        
        self.E_1 = self.model(self.E_1, dt*u)

        _log.warning("  control output calculated")
        _log.info("t: {}, t_ref: {}".format(t, t_ref))
        return (u, (t, self.tick, self.delay_est, self.y_estim[0], self.y_estim[1]), t_ref)

    action_priority = (timer_trigger, msg_trigger, ref_trigger, delay_trigger, update_smith, )
    requires = ['calvinsys.native.python-time', 'sys.timer.once']
