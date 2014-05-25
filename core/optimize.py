"""
Module includes the optimization related objects
"""
from abc import abstractmethod
from django.utils import simplejson
import numpy as np
from cvxopt.solvers import qp
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
    def optimize(self, cov, ret, **kwargs):
        pass


class ConstrainedReturnOptimizationPolicy(OptimizationPolicy):

    def optimize(self, cov, ret, **kwargs):
        """
        Optimization function that solves the convex quadratic optimization problem for the
        constrained return (minimum return) portfolio optimization problem.

        :param cov: the covariance matrix
        :type cov: numpy.array

        :param ret: the returns vector
        :type ret: numpy.array

        :param **kwargs: other keyword arguments, for ``ConstrainedReturnOptimizationPolicy`` the keyword ``min_return``
            must be provided with a value of type float

        :rtype: numpy.array
        :returns: the weights vector for the optimal portfolio allocation
        """
        # convert all matrices to cvxopt type matrices
        S = cvx.matrix(cov)
        n = np.shape(cov)[0]

        q = cvx.matrix(np.matrix(np.zeros((n,1))))

        # limit portfolio to 1 and the portfolio return to .35
        ones = np.matrix(np.ones((1,n)))
        A = cvx.matrix(np.vstack((ones, ret)))

        b = cvx.matrix(np.matrix([1.0, .35]).T)

        # no short-sell ($x_i \ge 0$)
        G = cvx.matrix(np.zeros((n,n)))
        G[::n+1] = -1.0
        h = cvx.matrix(np.matrix(np.zeros((n,1))))

        # solve with cvx opt
        soln = qp(S, q, G, h, A, b)

        #initialize the optimizer result object
        result = OptimizerResult()

        result._is_optimal = (soln.get("status") == "optimal")

        x_opt = np.matrix(soln['x'])
        x_opt = np.array(np.reshape(x_opt, (1,3)))[0]
        result._weights = x_opt

        return result


class OptimizerResult:
    """
    A class that encapsulates the results pertaining to a single optimization problem

    Class attributes:

    - weights       list    The weights vector resulting from the optimization problem
    - risk          float   The resulting risk (variance) for the optimal portfolio
    - return        float   The resulting return for the optimal portfolio
    - is_optimal    boolean If the resulting portfolio is optimal
    """

    _weights = []
    _risk = 0.0
    _return = 0.0
    _is_optimal = False

    def to_json(self):
        """
        Translate the contents (attributes) of the class to a JSON object format

        :returns: the JSON string
        :rtype: str
        """
        dc = {
            "weights": self._weights,
            "risk": self._risk,
            "return": self._return,
            "is_optimal": self._is_optimal
        }

        return simplejson.dumps(dc)
