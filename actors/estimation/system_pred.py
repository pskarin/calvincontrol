# -*- coding: utf-8 -*-
import sys
import numpy as np

from calvin.actor.actor import Actor, manage, condition, stateguard

class system_pred(Actor):
    """ Predict network delay
    TODO: Insert description, calculates one-step prediction of the C->P link.
    """

    @manage(['Q', 'R', 'x', 'P', 'x_p', 'P_p', 'A', 'C'])
    def init(self, sig_Q=10, sig_R=0.1):
        self.Q = sig_Q*np.eye(2)
        self.R = sig_R*np.eye(1)

        self.x = np.zeros((2, 1))
        self.P = np.eye(2)
        
        self.x_p = np.zeros((2, 1))
        self.P_p = np.eye(2)

        self.A = lambda h: np.array([[1.0 h], [0.0 1.0]])
        self.C = np.array([[1.0, 0.0]])

        self.time = None
        self.setup()

    def setup(self):
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']

    def did_migrate(self):
        self.setup()

    # y must at the moment be a (ny, 1) numpy array
    @condition(['y'],[])
    def inputy(self, y):
        self.y = np.append(y, self.y[:-1], axis=0)

    @condition([],['y_h'])
    def predict(self):
        
        # Update model with new measurement 
        T1 = self.R + np.matmul(self.C, np.matmul(self.P_p, self.C.T))
        K = self.matmul(self.P_p, self.C.T) * np.linalg.inv(T1) # Bad practice, but ok if S is scalar as in this case
        
        T2 = np.eye(self.n) - np.matmul(K, self.C)
        self.x = self.x_P + np.matmul(K, (self.y[0] - self.y_h)) 
        self.P = np.matmul(T2, np.matmul(self.P_p, T2.T)) + np.matmul(K, np.matmul(self.R, K.T))        

        self.r = np.append(self.y[0] - self.y_h, self.r[:-1], axis=0)

        # Generate new A, C matrices and a new one-step prediction
        self.A = np.eye(self.n)
        self.C = np.append(self.y, self.r, axis=0).T

        self.x_p = np.matmul(self.A, self.x)
        self.P_p = np.matmul(self.A, np.matmul(self.P, self.A.T)) + self.Q

        self.y_h = np.matmul(self.C, self.x_p)

        # What does this do?
        self.monitor_value = (self.y[0], self.y_h, self.r[0])

        return self.y_h

    action_priority = (inputy, predict,)
    requires = ['calvinsys.native.python-time']

# What is the difference between having two separate input, output function than having one and the same?
