"""
Module includes the optimization related objects
"""
from abc import abstractmethod
import numpy as np
import cvxopt as cvx

__author__ = 'Caner'

class Optimizer:

    _config = None
    _policy = None

    def __init__(self, config, policy):
        assert isinstance(config, OptimizerConfiguration)
        assert isinstance(policy, OptimizationPolicy)
        self._config = config
        self._policy = policy

    def optimize(self):
        self._policy.optimize(self._config._cov_matrix, self._config._ret_vector)



class OptimizerConfiguration:

    _cov_matrix = None
    _ret_vector = None

    def __init__(self, cov_matrix, ret_vector):
        assert isinstance(cov_matrix, np.array)
        assert isinstance(ret_vector, np.array)

        self._cov_matrix = cov_matrix
        self._ret_vector = ret_vector


class KnownInstrumentOptimizationProblem:
    pass

class OptimizationPolicy:

    _config = None

    @abstractmethod
    def optimize(self, cov, ret):
        pass


#class ConstrainedReturnOptimizationPolicy(OptimizationPolicy):
#
#    def optimize(self, cov, ret):
#    # convert all matrices to cvxopt type matrices
#        S = cvx.matrix(S_np)
#        q = cvx.matrix(np.matrix(np.zeros((n,1))))
#
#        # limit portfolio to 1 and the portfolio return to .35
#        A_ones = np.matrix(np.ones((1,n)))
#        A = cvx.matrix(np.vstack((ones, mu_r)))
#
#        b = cvx.matrix(np.matrix([1.0, .35]).T)
#
#        # no short-sell ($x_i \ge 0$)
#        G = cvx.matrix(np.zeros((n,n)))
#        G[::n+1] = -1.0
#        h = cvx.matrix(np.matrix(np.zeros((n,1))))
#
#        # solve with cvx opt
#        soln = qp(S, q, G, h, A, b)


