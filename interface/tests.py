from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.utils import simplejson
from interface.views import backtest


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