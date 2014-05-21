import datetime
from model.models import Instrument
import numpy as np

__author__ = 'Caner'

class InstrumentDataNotFoundException(BaseException):
    pass


class Tester:
    """
    The ``Tester`` class runs a backtest of a given instrument in a given time frame
    """

    configuration   = None
    start_datetime  = None
    end_datetime    = None
    price_matrix    = None

    def __init__(self, configuration, start_dt, end_dt, period):
        """
        Constructor method for the ``Tester`` class

        :param configuration: TesterConfiguration object, initialization parameters of the instruments
        :type configuration: core.backtest.TesterConfiguration

        :param start_dt: the start date time, defaults to a time in the distant past. If the available time is after
        the specified start time, the backtest will start from the earliest record available
        :type start_dt: datetime.datetime

        :param end_dt: the end date time, defaults to a time in the distant future. If the available time of instrument
        records ends before the specified time, the backtest will end at the latest record available
        :type end_dt: datetime.datetime

        :param period: the period for the instrument data that the backtest will be based on
        :type period: core.models.period
        """
        self.configuration = configuration
        # Start time and end time default to 1960 (way back) and 2050 (in distant future)
        self.start_datetime  = datetime.datetime(1960,01,01,00,00,00) if not start_dt else start_dt
        self.end_datetime    = datetime.datetime(2050,12,31,23,59,00) if not end_dt   else end_dt
        self.period = period

        # Retrieve price collections for each instrument
        price_collections = []

        # todo: must implement support for non-matching time frames

        for i in configuration.instruments:
            assert isinstance(i, Instrument)
            coll = i.get_bar_collection_timeframe(self.period, self.start_datetime, self.end_datetime)
            if not coll:
                raise InstrumentDataNotFoundException("Data for one of the requested instruments: %s, is not available. Backtest cannot run" % i.name)
            price_collections.append(np.array(coll))

        self._prices = price_collections


    def run(self):
        """
        Runs the backtest and provides the results

        .. warning:: no drawdown calculation, no support for short-sell
        :rtype: TesterResult
        """
        w = np.array(self.configuration.weights)
        try:
            price_matrix = np.vstack(self._prices).T

            # pfolio price vector
            pfolio = np.sum(w * price_matrix, axis=1)

            result = TesterResult()
            result._min_nominal = np.min(pfolio)
            result._max_nominal = np.min(pfolio)
            result._return_pct  = (pfolio[-1] - pfolio[0]) / pfolio[0]
            result._return_nominal = pfolio[-1] - pfolio[0]

            return result
        except:
            return None



class IllegalArgumentException(BaseException):
    pass

class TesterConfiguration():
    """
    Configuration object for the backtest (`Tester`)
    """
    instruments = [] # list object that includes the instrument objects
    weights     = [] # portfolio weights

    def __init__(self, instruments=None, weights=None):
        """
        Constructor, fails if the instruments or weights are null, their dimensions don't match, or the absval of weights
        does not add up to one (abs due to the fact that shortselling is allowed)

        :param instruments: a list of the instruments (`Instrument` instantiations) from which the backtest portfolio
        will be constructed
        :type instruments: list
        :param weights: the portfolio weights (as floating point numbers < 1) of the instruments in the portfolio. The numbers
        may include negative numbers (> -1) standing for shortselling
        :type weights: list
        """
        if instruments is None or weights is None:
            raise IllegalArgumentException("Arguments of type None are not allowed in TesterConfiguration")
        if len(instruments) != len(weights):
            raise IllegalArgumentException("Number of weights and instruments must match")

        arr = np.array(weights)
        if np.sum(np.absolute(arr)) > 1:
            raise IllegalArgumentException("The weights must add up to 1!")

        self.instruments = instruments
        self.weights     = weights

class TesterResult():
    """
    Backtest results
    """
    _return_pct          = 0
    _return_nominal      = 0
    _max_nominal         = 0
    _min_nominal         = 0

    def __init__(self, **kwargs):
        """

        """
        pass
