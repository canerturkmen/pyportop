"""
Module includes the optimization related objects
"""
from abc import abstractmethod
from django.utils import simplejson
from model.models import Instrument, Period
import numpy as np
from cvxopt.solvers import qp
import cvxopt as cvx

__author__ = 'Caner'

class Optimizer:
    """
    The ``Optimizer`` class is the object that encapsulates the portfolio optimization logic pertaining to a
    single portfolio optimization problem. Ideally, a new ``Optimizer`` instance is instantiated for every new
    problem.

    Class attributes:

    - _config       ``OptimizerConfiguration`` - the configuration object
    - _policy       ``OptimizationPolicy`` - the policy object
    """
    _config = None
    _policy = None

    def __init__(self, config, policy):
        """
        Constructor method for the Optimizer, which expects a configuration and policy object.

        :param config: the object which encapsulates the configuration (including the covariance matrix and
            return vector
        :type config: OptimizerConfiguration

        :param policy: the object which encapsulates the optimization "strategy"
        :type policy: OptimizationPolicy

        :returns: the constructed Optimizer
        :rtype: Optimizer
        """
        assert isinstance(config, OptimizerConfiguration)
        assert isinstance(policy, OptimizationPolicy)
        self._config = config
        self._policy = policy

    def optimize(self, **kwargs):
        """
        Solve the optimization problem and return the resulting OptimizerResult object

        :returns: the solution of the optimization, as an OptimizerResult object
        :rtype: OptimizerResult
        """

        return self._policy.optimize(self._config._cov_matrix, self._config._ret_vector, **kwargs)


class OptimizerConfiguration:
    """
    Class for encapsulating the "configuration" of an optimizer. The configuration includes the covariance
    matrix and the returns vector. The class has an attribute for each of these elements along with a
    constructor method expecting the same.
    """

    _cov_matrix = None
    _ret_vector = None

    def __init__(self, cov_matrix, ret_vector):
        """
        Constructor method for the ``OptimizerConfiguration`` class.

        :param cov_matrix: the covariance matrix for each of the instruments. If there are N instruments on which
            a portfolio optimization must be performed, this variable must be a matrix of NxN. The matrix must be
            square and symmetric
        :type cov_matrix: numpy.array

        :param ret_vector: the mean returns vector for each of the instruments. If there are N instruments on which
            portfolio optimization must be performed, this variable must be a matrix of 1xN or vector of N elements.
        :type ret_vector: numpy.array

        :returns: the configuration object
        :rtype: OptimizerConfiguration
        """
        # assert covariance matrix is square
        s = np.shape(cov_matrix)
        assert s[0] == s[1]

        # infer number of instruments from cov matrix
        n = s[0]

        # assert the cov matrix is symmetric
        assert np.allclose(cov_matrix, cov_matrix.T)

        # assert the number of elements in the returns vector equal to N
        assert n == np.shape(ret_vector)[0]

        self._cov_matrix = cov_matrix
        self._ret_vector = ret_vector


class KnownInstrumentOptimizationProblem:
    """
    The KnownInstrumentOptimizationProblem class encapsulates an optimization problem where the
    associated financial securities are already known to the system and some price data is
    available in the database.
    """

    def __init__(self, inst_array, start_dt, end_dt):
        """
        The constructor method for the class

        :param inst_array: is a list of strings that are instrument names, the portfolio optimization problem
            will run on these instruments
        :type inst_array: list

        :param start_dt: the start datetime for which the data will be pulled, calculating optimization
            parameters
        :type start_dt: datetime

        :param end_dt: the end datetime for which the data will be pulled, calculating optimization
            parameters
        :type end_dt: datetime
        """

        prices = []
        for iname in inst_array:
            i = Instrument.get_instrument(iname)
            price_i = i.get_bar_collection_timeframe(Period.get_period("H1"), start_dt, end_dt)
            price_x = map(lambda x: x.close, price_i)
            prices.append(price_x)

        z = []
        for i in prices:
            z.append(np.matrix(i).T)

        self._p_matrix = np.hstack(z)

    def prep_optimization_config(self):
        """
        The method prepares the optimization config, filling the internal `_config` variable by calculating
        the covariance matrix and mean return vector for the problem with the data provided

        The calculation logic was benchmarked against MATLAB financial toolbox
        """
        A = self._p_matrix

        retmx = A / np.vstack((A[0].astype(float), A[:-1].astype(float))) -1

        ret_vc = np.array(np.mean(retmx, axis=0))[0]
        cov_mx = np.cov(retmx, rowvar=0)

        self._config = OptimizerConfiguration(cov_mx, ret_vc)

    def optimize(self, **kwargs):
        """
        Run the prep logic, set up the `Optimizer` and run the optimizer to calculate the best portfolio
        with the price data in the given interval

        :param **kwargs: the keyword arguments that are passed to Optimizer.optimize and should include min_return
            for ConstrainedReturnOptimizationPolicy, specifying the minimum acceptable return

        :rtype: OptimizerResult
        :return: the optimization result
        """

        opt = Optimizer(self._config, ConstrainedReturnOptimizationPolicy())

        return opt.optimize(**kwargs)


class OptimizationPolicy:
    """
    OptimizationPolicy is an abstract class that defines an interface for all portfolio optimization
    policies. The three policies intended originally were:

    - risk-return weighted optimization (find an optimal spot on the efficient frontier with respect to a risk-return
    weighting factor
    - constrained risk optimization (find an optimal portfolio given a maximum risk that will be tolerated, currently
    not implemented since the problem is actually a semidefinite programming problem)
    - constrained return optimization (currently implemented, the policy that finds the minimum risk portfolio for a
    set return level on the efficient frontier)
    """

    @abstractmethod
    def optimize(self, cov, ret, **kwargs):
        pass


class ConstrainedReturnOptimizationPolicy(OptimizationPolicy):
    """
    Strategy design pattern-like class inheriting from the abstract ``OptimizationPolicy`` class (which is
    essentially equivalent to a Java interface
    """

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

        b = cvx.matrix(np.matrix([1.0, kwargs.get("min_return")]).T)

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


        ret_calc = np.matrix(x_opt) * np.matrix(ret).T
        result._return = ret_calc[0,0]

        w_calc = np.matrix(x_opt)
        result._risk = np.sqrt((w_calc * (w_calc * cov).T)[0,0])

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
            "weights": list(self._weights),
            "risk": self._risk,
            "return": self._return,
            "is_optimal": self._is_optimal
        }

        return simplejson.dumps(dc)
