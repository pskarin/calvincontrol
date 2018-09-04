# -*- coding: utf-8 -*-
import sys
from calvin.actor.actor import Actor, manage, condition, stateguard, calvinsys
from calvin.utilities.calvinlogger import get_actor_logger
from collections import deque
import numpy as np
_log = get_actor_logger(__name__)


class PIDClock(Actor):
    '''
    Generic PID

    Inputs:
        y: Measured value
        y_ref: Reference point
    Outputs:
        v: Control value
    '''

    @manage(['td', 'ti', 'tr', 'kp', 'ki', 'kd', 'n', 'beta', 'i', 'd',
             'y_old', 'y_prev_t', 'timer', 'period', 'started', 'tick',
             'msg_estim_q','max_q', 'y_estim', 'y_ref', 'name'])
    def init(self, td=1., ti=5., tr=10., kp=-.2, ki=0., kd=0., n=10.,
             beta=1., period=0.05, max_q=1000, name="Name"):
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
        self.name = name

        self.y_old = 0.

        self.started = False
        self.tick = 0
        self.setup()
        self.y_prev_t = self.time.timestamp()

        # Message queue (deque is thread-safe no need for a lock)
        self.msg_q = deque([], maxlen=self.max_q)
        # Estimator
        self.msg_estim_q = deque([], maxlen=self.max_q)

        self.y_estim = 0
        self.y_ref = (0, (self.y_prev_t, self.tick), (0.0, 0.0))

    def setup(self):
        self.timer = calvinsys.open(self, "sys.timer.repeating")
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']
        self.qt = self.time.timestamp()
        _log.warning("Set up")
        Cont = calvinsys.can_write(self.timer)
        if not Cont:
            _log.warning("  Can't write timer")
        elif not self.started:
            _log.warning("  write timer")

    @stateguard(lambda self: (not self.started
                              and calvinsys.can_write(self.timer)))
    @condition([], [])
    def start_timer(self):
        _log.warning("Start Timer")
        self.started = True
        calvinsys.write(self.timer, self.period)
        return

    @stateguard(lambda self: calvinsys.can_read(self.timer))
    @condition([], ['v'])
    def timer_trigger(self):
        _log.warning(self.name + "; Tick: {}".format(self.tick))
        _log.debug('Take values from buffer on timer trigger.')
        calvinsys.read(self.timer)
        self.tick += 1

        if len(self.msg_q) > 0:
            _log.warning("  Read buffer and estimate y")
            self.y_estim = self.estimator_run()
        else:
            _log.warning("  buffer empty, use old estimate")
            self.y_estim = self.y_old

        v = self.calc_output()
        _log.warning(self.name + "; calculation complete, returning")
        return (v, )

    # @stateguard(lambda self: (calvinsys.can_read(self.y)))
    @condition(['y'], [])
    def msg_trigger(self, y):
        ''' Save token messages received for future use '''
        _log.info(self.name + "; buffering measurements: {}".format(y))
        self.msg_q.append(y) # Save entire input for timestamps
        return

    @condition(['y_ref'], [])
    def ref_trigger(self, y_ref):
        _log.warning(self.name + "; updating reference: {}".format(y_ref))
        if self.y_ref[1][0] < y_ref[1][0]: # Only update when new reference is more fresh
            self.y_ref = y_ref
        return

    # When actuating, calculate the real delay using timestamp and pair it with its tick. Send it
    # along with the next value
    #def estimate_delay(self):
    #    for k in range(len(self.msg_estim_q)):
    #        # (true delay, tick)
    #        arrival_tuple = self.msg_estim_q[k][3]

    def estimator_run(self, mode='average'):

        ''' Estimate the next tick values using the saved received ones '''
        # Move content of msg_q to estim_q
        self.msg_estim_q.extend(self.msg_q)
        self.msg_q.clear()
        
        #h = estimate_delay()

        _log.warning("  Estimate using {}, queue length: {}".format(
                     mode, len(self.msg_estim_q)))
        if mode == 'extrapolate':
            # Use numpy and do curve fitting of the values stored
            est_weights = np.polyfit(x=range(0, len(self.msg_estim_q)),
                                     y=self.msg_estim_q,
                                     deg=1)
            est_fct = np.poly1d(est_weights)
            estimated = est_fct(self.tick + 1)
        elif mode == 'average':
            estimated = sum([msg[0] for msg in self.msg_estim_q]) / len(self.msg_estim_q)
        else:  # use last received value
            estimated = self.msg_estim_q[-1]

        self.msg_estim_q.clear()  # Clear the queue now that we used it
        _log.warning("  Estimated y is: {} ({})".format(estimated, mode))
        return estimated

    def did_migrate(self):
        self.setup()
    
    def calc_output(self):
        y_ref, ref_t, _  = self.y_ref
        _log.warning("CHECK ref_t: {}".format(ref_t))
        _log.warning("  Read y estimation")
        y = self.y_estim
        y_t = self.time.timestamp()
        dt = y_t - self.y_prev_t
        self.y_prev_t = y_t

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

        _log.warning("  control output calculated")
        _log.info(y_t, ref_t)
        return (u, (y_t, self.tick), ref_t)

    action_priority = (start_timer, timer_trigger, msg_trigger, ref_trigger, )
    requires = ['calvinsys.native.python-time', 'sys.timer.repeating']
