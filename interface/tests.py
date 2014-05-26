from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.utils import simplejson
from interface.views import backtest, optimize


class BacktestAPITest(TestCase):

    fixtures = ["dump.json"]

    def test_fixture_scenario(self):
        req = HttpRequest()

        x = {
            "instruments": ["EURUSD", "GBPUSD", "GBPJPY"],
            "weights": [0.3, 0.3, 0.4],
            "period": "H1",
            "start-date": "2014-05-21T13:00:00",
            "end-date": "2014-05-22T13:00:00"
        }
        req._body = simplejson.dumps(x)

        res = backtest(req)

        result = simplejson.loads(res._get_content())

        self.assertEqual(res.status_code, 200)
        self.assertAlmostEqual(result.get("return_nominal"), 0.00205)

    def test_nonmatching_vectors(self):
        req = HttpRequest()
        x = {
            "instruments": ["EURUSD", "GBPUSD", "GBPJPY"],
            "weights": [0.3, 0.3],
            "period": "H1",
            "start-date": "2014-05-21T13:00:00",
            "end-date": "2014-05-22T13:00:00"
        }

        req._body = simplejson.dumps(x)

        res = backtest(req)

        self.assertEqual(res.status_code, 200)
        result = simplejson.loads(res._get_content())

        self.assertIsNotNone(result.get("error", None))

    def test_corrupted_date(self):
        req = HttpRequest()
        x = {
            "instruments": ["EURUSD", "GBPUSD", "GBPJPY"],
            "weights": [0.3, 0.3, 0.4],
            "period": "H1",
            "start-date": "2014-05-asdfasdf00:00",
            "end-date": "2014-05-22T13:00:00"
        }

        req._body = simplejson.dumps(x)

        res = backtest(req)

        self.assertEqual(res.status_code, 200) # must fail gracefully

        result = simplejson.loads(res._get_content())

        self.assertIsNotNone(result.get("error", None))

    def test_invalid_instrument(self):
        req = HttpRequest()

        x = {
            "instruments": ["EURUSD", "GBPUSD", "AUSSIE"],
            "weights": [0.3, 0.3, 0.4],
            "period": "H1",
            "start-date": "2014-05-21T13:00:00",
            "end-date": "2014-05-22T13:00:00"
        }
        req._body = simplejson.dumps(x)

        res = backtest(req)

        self.assertEqual(res.status_code, 200) # must fail gracefully

        result = simplejson.loads(res._get_content())

        self.assertIsNotNone(result.get("error", None))


class OptimizeAPITest(TestCase):

    fixtures = ["dump.json"]

    initial_data = {
            "covariance": [[1.23, 1.56, 1.41],
                           [1.56, 1.9, 2.0],
                           [1.41, 2.0, 1.4]],
            "returns": [0.9, 1.2, 1.4],
            "min_return": 1.2
    }


    def test_fixture_optimize_scenario(self):
        # test the scenario for a normal optimization scenario

        req = HttpRequest()
        req._body = simplejson.dumps(self.initial_data)

        res = optimize(req)

        self.assertEqual(res.status_code, 200)

    def test_nonsquare_cov_matrix(self):
        # fail, provided a non-square covariance matrix

        req = HttpRequest()
        data = self.initial_data.copy()
        data.update({"covariance": [[1,2,3], [4,5,6]]})

        req._body = simplejson.dumps(data)

        res = optimize(req)

        self.assertEqual(res.status_code, 200)

        result = simplejson.loads(res._get_content())

        self.assertIsNotNone(result.get("error"))
        self.assertContains(res, "square") # the error message must talk about squares

    def test_nonsymmetric_cov_matrix(self):
        # fail, provided a non-symmetric covariance matrix

        req = HttpRequest()
        data = self.initial_data.copy()
        data.update({"covariance": [[1,2,3], [4,5,6], [7,8,9]]})

        req._body = simplejson.dumps(data)

        res = optimize(req)

        self.assertEqual(res.status_code, 200)

        result = simplejson.loads(res._get_content())

        self.assertIsNotNone(result.get("error"))
        self.assertContains(res, "symmetric") # the error message must talk about being symmetric

    def test_nonmatching_dimensions(self):
        # fail if mean-return vector and covar matrix have non matching dimensions

        req = HttpRequest()
        data = self.initial_data.copy()
        data.update({"returns": [2, 3]})

        req._body = simplejson.dumps(data)

        res = optimize(req)

        self.assertEqual(res.status_code, 200)

        result = simplejson.loads(res._get_content())

        self.assertIsNotNone(result.get("error"))
        self.assertContains(res, "dimensions") # the error message must talk about dimensions

    def test_missing_parameter(self):
        # fail if one of the parameters is missing

        for i in self.initial_data.keys():
            data = self.initial_data.copy()
            del data[i] # remove the key

            req = HttpRequest()
            req._body = simplejson.dumps(data)

            res = optimize(req)

            self.assertEqual(res.status_code, 200)

            result = simplejson.loads(res._get_content())

            self.assertIsNotNone(result.get("error"))
            self.assertContains(res, "missing") # the error message must talk about a missing parameter
