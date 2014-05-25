import random
from core.optimize import OptimizerConfiguration, ConstrainedReturnOptimizationPolicy, OptimizationPolicy, Optimizer, KnownInstrumentOptimizationProblem
from django.test import TestCase
from django.utils.timezone import utc
from model.models import *
from core.backtest import *

def fill_dummy_data(ticker_arr):
    """
    :param ticker_arr: list of symbols to create dummy data for
    :type ticker_arr: list
    """

    p = Period(name="H1")
    p.save()

    instruments = []
    for i in range(len(ticker_arr)):
        inst = Instrument(name=ticker_arr[i], description="NA", is_forex=True)
        inst.save()

        price = 1.4567 + i * .1
        initial_date = datetime.datetime(2014,05,01,hour=12,minute=00,second=00, tzinfo=utc)
        for x in range(1000):
            tstamp = initial_date + (x * timedelta(hours=1))
            price += random.randint(1,3) * random.randint(-1,1) * random.randint(0, 10) / 1e4
            ibar = IBar(start_time = tstamp, open=price, high=price, low=price, close=price, period=p, instrument=inst)
            ibar.save()

class BacktestTest(TestCase):

    fixtures = ["dump.json"]
    _config = None
    _ls = ["EURUSD", "GBPUSD", "GBPJPY"]


    def test_config_initialize(self):

        config = TesterConfiguration(self._ls, [.3, .3, .4])
        self.assertIsNotNone(config)


    def test_backtest_initialize(self):
        config = TesterConfiguration(self._ls, [.3, .3, .4])

        #noinspection PyTypeChecker
        self._tester = Tester(config, None, None, Period.get_period("H1"))

        self.assertIsInstance(self._tester._prices, list)

    def test_result_returned(self):
        config = TesterConfiguration(self._ls, [.3, .3, .4])
        a = datetime.datetime(2014,05,21,13,00,00)
        b = datetime.datetime(2014,05,22,13,00,00)
        self._tester = Tester(config, a, b, Period.get_period("H1"))
        result = self._tester.run()

        self.assertIsInstance(result, TesterResult)

    def test_result_correct(self):
        config = TesterConfiguration(self._ls, [.3, .3, .4])
        a = datetime.datetime(2014,05,21,13,00,00)
        b = datetime.datetime(2014,05,22,13,00,00)
        self._tester = Tester(config, a, b, Period.get_period("H1"))
        result = self._tester.run()

        self.assertAlmostEqual(result._min_nominal, 1.5560, places=3)
        self.assertAlmostEqual(result._max_nominal, 1.5588, places=3)
        self.assertAlmostEqual(result._return_nominal, 0.0020, places=3)
        self.assertAlmostEqual(result._return_pct, 0.0013, places=3)





class OptimizerConfigurationTest(TestCase):
    # Test the following cases:
    # non-square matrix
    # non-symmetric matrix
    # return vector and matrix don't match in shape
    # good configuration

    def test_nonsquare_matrix(self):
        cov_matrix = np.array([[1,2,3],[3,4,5]])
        ret_vector = np.array([1,4,5])
        self.assertRaises(AssertionError, OptimizerConfiguration, cov_matrix, ret_vector)

    def test_nonsymmetric_matrix(self):
        cov_matrix = np.array([[1,2,3],[3,4,5], [4,5,6]])
        ret_vector = np.array([1,4,5])
        self.assertRaises(AssertionError, OptimizerConfiguration, cov_matrix, ret_vector)

    def test_nonmatching_dimensions(self):
        cov_matrix = np.array([[1,2,3],[3,4,5], [4,5,6]])
        ret_vector = np.array([1,4])
        self.assertRaises(AssertionError, OptimizerConfiguration, cov_matrix, ret_vector)

    def test_normal_conditions(self):
        cov_matrix = np.array([[1,2,3],[2,4,5], [3,5,6]])
        ret_vector = np.array([1,4,5])
        oc = OptimizerConfiguration(cov_matrix, ret_vector)
        self.assertIsNotNone(oc)

class OptimizerTest(TestCase):
    # Test the Optimizer itself
    # Test cases are derived with MATLAB's portopt

    _covmx = np.array([[1.2, 1.3, 1.5],
                       [1.3, .8, .9],
                       [1.5, .9, 1.7]]) # covariance matrix
    _retvc = np.array([0.5, 0.9, 1.4])

    def test_initalize_config(self):
        config = OptimizerConfiguration(self._covmx, self._retvc)
        self.assertIsNotNone(config)

    def test_initialize_policy(self):
        self._policy = ConstrainedReturnOptimizationPolicy()
        self.assertIsInstance(self._policy, OptimizationPolicy)

    def test_initialize_optimizer(self):
        config = OptimizerConfiguration(self._covmx, self._retvc)
        self._policy = ConstrainedReturnOptimizationPolicy()
        self._optimizer = Optimizer(config, self._policy)
        self.assertIsNotNone(self._optimizer)

    def test_run_optimizer_normal(self):
        config = OptimizerConfiguration(self._covmx, self._retvc)
        self._policy = ConstrainedReturnOptimizationPolicy()
        self._optimizer = Optimizer(config, self._policy)

        result = self._optimizer.optimize(min_return = 1.2)
        self.assertTrue(result._is_optimal)
        self.assertAlmostEqual(result._return, 1.2, places=2)
        self.assertAlmostEqual(result._risk, 1.0826, places=2)

        w = list(result._weights)
        self.assertAlmostEqual(w[2], 0.6, places=2)

    def test_run_optimizer_boundary(self):
        # run the optimizer on the upper boundary (max return that can be achieved)

        config = OptimizerConfiguration(self._covmx, self._retvc)
        self._policy = ConstrainedReturnOptimizationPolicy()
        self._optimizer = Optimizer(config, self._policy)

        result = self._optimizer.optimize(min_return = 1.4)
        self.assertTrue(result._is_optimal)
        self.assertAlmostEqual(result._return, 1.4,places=2)
        self.assertAlmostEqual(result._risk, 1.3038,places=2)

    def test_run_optimizer_suboptimal(self):

        config = OptimizerConfiguration(self._covmx, self._retvc)
        self._policy = ConstrainedReturnOptimizationPolicy()
        self._optimizer = Optimizer(config, self._policy)

        result = self._optimizer.optimize(min_return = 1.5)
        self.assertFalse(result._is_optimal)

class KnownInstrumentTester(TestCase):

    fixtures = ["dump.json"]

    def test_config_calculation(self):
        a = datetime.datetime(2014,05,21,13,00,00)
        b = datetime.datetime(2014,05,22,13,00,00)
        prob = KnownInstrumentOptimizationProblem(["EURUSD", "GBPUSD", "GBPJPY"], a,b)

        prob.prep_optimization_config()

        r= prob._config._ret_vector
        print r

        self.assertAlmostEqual(r[0], 0.0000709)

    def test_config_covar(self):
        a = datetime.datetime(2014,05,21,13,00,00)
        b = datetime.datetime(2014,05,22,13,00,00)
        prob = KnownInstrumentOptimizationProblem(["EURUSD", "GBPUSD", "GBPJPY"], a,b)

        prob.prep_optimization_config()

        c = prob._config._cov_matrix
        print c[0,0]

        self.assertAlmostEqual(c[0,0], 0.2653e-6 )

    def test_known_optimize(self):
        a = datetime.datetime(2014,05,21,13,00,00)
        b = datetime.datetime(2014,05,22,13,00,00)
        prob = KnownInstrumentOptimizationProblem(["EURUSD", "GBPUSD", "GBPJPY"], a,b)

        prob.prep_optimization_config()

        res = prob.optimize(min_return=1.0e-4)
        # todo: compared to matlab, this one is slightly off the mark
        self.assertAlmostEqual(res._risk, 4.796719437920476e-04, places=4)
