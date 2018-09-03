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
             'y_old', 'y_prev_t', 'timer', 'period', 'started', 'tick','msg_estim_q','max_q'])
    def init(self, td=1., ti=5., tr=10., kp=-.2, ki=0., kd=0., n=10.,
             beta=1., period=0.05, max_q=1000):
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

        self.y_old = 0.

        self.started = False
        self.tick = 0
        self.setup()
        self.y_prev_t = self.time.timestamp()

        # Message queue (deque is thread-safe no need for a lock)
        self.msg_q = deque([], maxlen=self.max_q)
        # Estimator
        self.msg_estim_q = deque([], maxlen=self.max_q)
        self.y_estim = None

    def setup(self):
        self.timer = calvinsys.open(self, "sys.timer.repeating")
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']
        self.qt = self.time.timestamp()
        _log.warning("Set up")
        #Cont = calvinsys.can_write(self.timer)
        #if not Cont:
         #   _log.warning("Can't write timer")
        #elif not self.started:
         #   _log.warning("write timer")

    @stateguard(lambda self: (not self.started
                              and calvinsys.can_write(self.timer)))
    @condition([], [])
    def start_timer(self):
        _log.warning("Start Timer")
        self.started = True
        calvinsys.write(self.timer, self.period)
        return (self.tick, )

    @stateguard(lambda self: calvinsys.can_read(self.timer))
    @condition([], [])
    def timer_trigger(self):
        _log.debug('Take values from buffer on timer trigger.')
        calvinsys.read(self.timer)
        self.tick += 1
        _log.warning("Tick: {}".format(self.tick))
        if len(self.msg_q) > 0:
        	self.y_estim = self.estimator_run()
                _log.warning("Read buffer and estimate y")
        else:
        	self.y_estim = self.y_old
                _log.warning("buffer empty, use old estimate")
        return

    #@stateguard(lambda self: (calvinsys.can_read(self.y)))
    @condition(['y'], [])
    def msg_trigger(self, y):
        ''' Save token messages received for future use '''
        _log.info('Save values to buffer on msg receive.')
       # calvinsys.read(self.y)
        self.y, _y_t, _tick = y
        _log.warning("y:{}".format(self.y))
        self.msg_q.append(self.y)
        _log.warning("queue length: {}".format(len(self.msg_q)))
        return

    def estimator_run(self, mode = 'average'):
        ''' Estimate the next tick values using the saved received ones '''
        # Move content of msg_q to estim_q
        self.msg_estim_q.extend(self.msg_q)
        self.msg_q.clear()

        _log.warning("Estimate using {}, queue length: {}".format(
                     mode, len(self.msg_estim_q)))
        if mode == 'extrapolate':
            # Use numpy and do curve fitting of the values stored
            est_weights = np.polyfit(x=range(0, len(self.msg_estim_q)),
                                     y=self.msg_estim_q,
                                     deg=1)
            est_fct = np.poly1d(est_weights)
            estimated = est_fct(self.tick + 1)
        elif mode == 'average':
            estimated = sum(self.msg_estim_q) / len(self.msg_estim_q)
        else:  # use last received value
            estimated = self.msg_estim_q[-1]

        self.msg_estim_q.clear()  # Clear the queue now that we used it
        _log.warning("Estimated y is: {} ({})".format(estimated, mode))
        return estimated

    def did_migrate(self):
        self.setup()

#    def pre_condition_wrapper(self):
#        """
# 		 NOTE! The algorithm at this point assumes
# 		 that there are only two queues!
# 		 """
#        isready = True
#        keys = self.inports.keys()
#        discarded = {}
#        for k in keys: discarded[k] = 0
#        for xk,xv in self.inports.iteritems():
#            if xv.num_tokens() > 0:
#                top = xv.get_token_from_top(0).value
#                for yk in [k for k in keys if not k == xk]:
#                    yv = self.inports[yk]
#                    cont = True
#                    while yv.num_tokens() > 1 and cont:
#                        yt0 = yv.get_token_from_top(0).value
#                        yt1 = yv.get_token_from_top(1).value
#                        if abs(yt0[1]-top[1]) > abs(yt1[1]-top[1]):
#                            yv.read()
#                            discarded[yk] += 1
#                        else:
#                            cont = False
#            else:
#                isready = False # Some queue is empty
#        if isready:
#            mintokens = min([x.num_tokens() for x in self.inports.values()])
#            for xk in keys:
#                xv = self.inports[xk]
#                for r in range(0, mintokens-1):
#                    xv.read()
#                    discarded[xk] += 1
#                self.log_queue_precond(xk, discarded[xk],
#                                       xv.get_token_from_top(0).value[1])
	# @stateguard(lambda self: calvinsys.can_read(self.y_estim))
    @condition(['y_ref'], ['v'])
    def cal_output(self, yt_ref):
        # Time management - for event based control
        y_ref, ref_t, tick = yt_ref
        # y, y_t, _tick = yt
        # calvinsys.read(self.y_estim)
        _log.warning("Read y estimation")
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
        v = self.kp * (self.beta * y_ref - y) + self.i + self.d

        # I
        self.i += (self.ki * dt / self.ti) * e * (dt / self.tr) * (y - v)

        # Update state
        self.y_old = y

        self.monitor_value = v

        _log.warning("control output calculated")
        _log.info(y_t, ref_t)
        return ((v, y_t + ref_t, self.tick), )

    action_priority = (start_timer, timer_trigger, msg_trigger, cal_output)
    requires = ['calvinsys.native.python-time', 'sys.timer.repeating']
