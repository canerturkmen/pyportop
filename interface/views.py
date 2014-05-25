"""
The ``views`` module includes the REST API function implementations for the POM software. Their corresponding
documentation are intended as REST API documentations and may be found below.
"""


import dateutil.parser
from core.backtest import TesterConfiguration, Tester
from core.optimize import *
from django.http import HttpResponse

# Create your views here.
from django.utils import simplejson as json
from django.views.decorators.csrf import csrf_exempt
from model.models import Period

@csrf_exempt
def backtest(req):
    """
    View controller for the REST API implementation of the backtest function.


    .. http:post:: /backtest/

        :jsonparam array instruments: list of instrument names
        :jsonparam array weights: list of floating point numbers (JSON Array) for the portfolio weights
        :jsonparam string start-date: Start date time for the backtest in ISO Datetime format
        :jsonparam string end-date: End date time for the backtest in ISO Datetime format
        :jsonparam string period: The period specifier ("H1", "M5", etc.)

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/javascript

            {
                "return_pct": 0.23, //the portfolio return in ratio terms
                "return_nominal": 230, //the portfolio return in nominal terms
                "max_nominal": 320, //the maximum nominal value of the portfolio in the test timeframe
                "min_nominal": 120 // the minimum nominal value of the portfolio in the test timeframe
            }
    """
    data = json.loads(req.body)
    config = TesterConfiguration(instruments=data.get("instruments"),
                                 weights=data.get("weights"))

    start_dt = dateutil.parser.parse(data.get("start-date"))
    end_dt  = dateutil.parser.parse(data.get("end-date"))

    period = Period.get_period(data.get("period"))

    # initialize the tester
    tester = Tester(config, start_dt, end_dt, period)

    # run the tester
    result = tester.run()

    return HttpResponse(result.stringify(), mimetype="application/json")

@csrf_exempt
def optimize(req):
    """
    View controller for the REST API implementation of the portfolio optimization function. The current API
    function solves a constrained return optimization problem (minimizing risk), by taking a covariance matrix
    and returns vector.

    The covariance matrix and returns vector must be provided to the API in the notations given below, and the
    ordering of instruments in the matrix and the returns vector MUST be the same.

    .. http:post:: /optimize/

        :jsonparam array covariance: the covariance matrix, must be given as an array of arrays, with each array
            representing a row of the covariance matrix. The matrix must be a square matrix of at least 2x2
        :jsonparam array returns: array of floats, each pertaining to the return of a certain instrument
        :jsonparam float min_return: for the constrained return optimization problem, a minimum acceptable return for
            the portfolio must be presented. As of the current version of the software, this is the only "policy" the
            optimizer works with. As such, this parameter is mandatory and must be provided in order for the
            interface to respond.

        **Example request**:

        .. sourcecode:: http

            POST /optimize/ HTTP/1.1
            Host: example.com
            Accept: application/json, text/javascript

            {
                "covariance": [[1.23, 1.56, 1.41],
                                [1.56, 1.9, 2.0],
                                [1.41, 2.0, 1.4]], // the covariance matrix, each sub-array corresponds to a row
                "returns": [0.9, 1.2, 1.4]
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/javascript

            {
                "weights": [0, 0.8, 0.2]
            }
    """
    data = json.loads(req.body)

    cov_mx = np.array(data.get("covariance"))
    ret_vc = np.array(data.get("returns"))

    if data.get("min_return"):
        policy = ConstrainedReturnOptimizationPolicy()
        config = OptimizerConfiguration(cov_mx, ret_vc)

        opt = Optimizer(config, policy)
        soln = opt.optimize(min_return = data.get("min_return"))

        return HttpResponse(soln.to_json(), mimetype="application/json")
    else:
        # normally other policies should appear here
        return HttpResponse("You must provide a 'min_return' parameter", mimetype="application/json")
