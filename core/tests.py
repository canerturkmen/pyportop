import random
from core.optimize import OptimizerConfiguration
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
            ibar = IBar(start_time = tstamp, open=price, high=price, low=price, close=price, period=p, instrument=i)
            ibar.save()

class BacktestTest(TestCase):

    _config = None
    _ls = ["EURUSD", "GBPJPY", "GBPUSD"]

    def test_data_initialize(self):
        fill_dummy_data(self._ls)

    def test_config_initialize(self):
        self._config = TesterConfiguration()
        instr_array = map(lambda x : Instrument.get_instrument(x),  self._ls)
        self._config.instruments = instr_array
        self._config.weights = [.3, .3, .4]

    def test_backtest_initialize(self):
        #noinspection PyTypeChecker
        self._tester = Tester(self._config, None, None, Period.get_period("H1"))

        self.assertIsInstance(self._tester._prices, list)
        self.assertIsInstance(self._tester._prices[0], np.array)

    def test_result_returned(self):
        result = self._tester.run()

        self.assertIsInstance(result, TesterResult)


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

#class OptimizerTest(TestCase):
#    # Test the Optimizer itself
#
#    _covmx = None # covariance matrix
#    _