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
        measured_delay: The measured true delay
    Outputs:
        v: Control value
    '''

    @manage(['td', 'ti', 'tr', 'kp', 'ki', 'kd', 'n', 'beta', 'i', 'd',
             'y_old', 't_old', 't_old_meas', 'timer', 'period', 'started', 
             'tick', 'y_estim', 'y_ref', 'name', 'delay_tick', 'delay_est',
             'x', 'P'])
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
        self.delay_tick = 0
        self.delay_est = 0

        self.y_old = 0.

        self.x = np.zeros((2, 1))
        self.P = np.eye(2)

        self.started = False
        self.tick = 0
        self.setup()
        self.t_old = self.time.timestamp()
        self.t_old_meas = self.time.timestamp()

        # Message queue (deque is thread-safe no need for a lock)
        #self.msg_q = deque([], maxlen=self.max_q)
        # Estimator
        #self.msg_estim_q = deque([], maxlen=self.max_q)

        self.y_estim = 0
        self.y_ref = (0, (self.y_prev_t, self.tick, 0.0), (0.0, 0.0, 0.0))

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
        
        """
        if len(self.msg_q) > 0:
            _log.warning("  Read buffer and estimate y")
            self.y_estim = self.estimator_run()
        else:
            _log.warning("  buffer empty, use old estimate")
            self.y_estim = self.y_old
        """
        self.estimator_run()
        v = self.calc_output()
        _log.warning(self.name + "; calculation complete, returning")
        return (v, )

    # @stateguard(lambda self: (calvinsys.can_read(self.y)))
    @condition(['y'], [])
    def msg_trigger(self, y):
        #''' Save token messages received for future use '''
        #_log.info(self.name + "; buffering measurements: {}".format(y))
        #self.msg_q.append(y) # Save entire input for timestamps

        # Update states using the measurement

        # calculate the time step, if it is negative corresponding to a previous value, 
        # then return.
        h = y[1] - self.t_old_meas
        if h < 0:
            return

        sig_Q = 0.01
        sig_R = 0.0001

        A = np.array([[1, h], [0, 1]])
        C = np.array([1, 0])
        Q = sig_Q*np.eye(2)
        R = sig_R*np.eye(1)

        xp = A.dot(self.x)
        Pp = A.dot(self.P).dot(A.T) + (h**2)*Q

        err = y[0] - C.dot(self.x)
        S = C.dot(Pp).dot(C.T) + R
        K = Pp.dot(C.T).dot(inv(S))
        self.x = xp + K.dot(err)
        self.P = (np.eye(2) - K.dot(C)).dot(Pp).dot((np.eye(2) - K.dot(C)).T) + K.dot(R).dot(K.T)

        self.t_old_meas = y[1]
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


    # When actuating, calculate the real delay using timestamp and pair it with its tick. Send it
    # along with the next value
    #def estimate_delay(self):
    #    for k in range(len(self.msg_estim_q)):
    #        # (true delay, tick)
    #        arrival_tuple = self.msg_estim_q[k][3]


    # For a kalman filter, use a second order integrator as the linear model (position and speed as the 
    # unknown parameters that should be estimated). For an incomming tick k, estimate x_k from
    # x_k-1 and correct with y_k. When the estimator should run, use the model, the delay
    # estimation, the delay from the tick k  and x_k to estimate y_t. 
    def estimator_run(self, mode='average'):

        """
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
        """

        h = self.delay_est + (self.time.timestamp() - self.old_time())
        A = np.array([[1, h], [0, 1]])
        xp = A.dot(self.x)
        self.y_estim = xp[0]
        return #xp[0]

    def did_migrate(self):
        self.setup()
    
    def calc_output(self):
        y_ref, t_ref, _  = self.y_ref
        y = self.y_estim
        t = self.time.timestamp()
        dt = y_t - self.t_old
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

        _log.warning("  control output calculated")
        _log.info(y_t, t_ref)
        return (u, (y_t, self.tick, self.delay_est), t_ref)

    action_priority = (start_timer, timer_trigger, msg_trigger, ref_trigger, delay_trigger, )
    requires = ['calvinsys.native.python-time', 'sys.timer.repeating']
