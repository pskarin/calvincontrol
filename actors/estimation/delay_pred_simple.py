# -*- coding: utf-8 -*-
import sys
import numpy as np

from calvin.actor.actor import Actor, manage, condition, stateguard

class delay_pred(Actor):
    """ Predict network delay
    TODO: Insert description, calculates one-step prediction of the C->P link.
    """

    @manage(['D', 'alpha', 't_end'])
    def init(self, alpha=0.2):

        self.D = 0
        self.alpha = alpha
        self.t_end = 0

        self.time = None
        self.setup()

    def setup(self):
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']

    def did_migrate(self):
        self.setup()

    # d whould be a vector of tuples, (previous delays, timestamps) 
    @condition(['d'],[])
    def inputVal(self, d):
        
        # Extract values whose timestamps are greater than the last used value
        d_use = []
        for k in range(length(d)):
            if d[k][1] > self.t_end:
                d_use.append(d[k])

        # Pseudocode, sort in ascending order after timestamp.
        SORT(d_use, axis=2)
        for k in range(length(d_use)):
            self.D = self.alpha*d_use[k][0] + (1 - self.alpha)*self.D

        # Update final time
        self.t_end = d_use[-1][1]
        

    @condition([],['d_h'])
    def predictDelay(self):
        return self.D

    action_priority = (inputVal, predictDelay,)
    requires = ['calvinsys.native.python-time']

# What is the difference between having two separate input, output function than having one and the same?
