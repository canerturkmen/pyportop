import datetime

__author__ = 'Caner'

class Tester:
    """
    The ``Tester`` class runs a backtest of a given instrument in a given time frame
    """

    instrument      = None
    start_datetime  = None
    end_datetime    = None

    def __init__(self, instrument, start_dt, end_dt, period):
        """
        Constructor method for the ``Tester`` class

        :param instrument: the instrument for which the backtest will run
        :type instrument: core.models.Instrument

        :param start_dt: the start date time, defaults to a time in the distant past. If the available time is after
        the specified start time, the backtest will start from the earliest record available
        :type start_dt: datetime.datetime

        :param end_dt: the end date time, defaults to a time in the distant future. If the available time of instrument
        records ends before the specified time, the backtest will end at the latest record available
        :type end_dt: datetime.datetime

        :param period: the period for the instrument data that the backtest will be based on
        :type period: core.models.period
        """
        self.instrument = instrument
        # Start time and end time default to 1960 (way back) and 2050 (in distant future)
        self.start_datetime  = datetime.datetime(1960,01,01,00,00,00) if not start_dt else start_dt
        self.end_datetime    = datetime.datetime(2050,12,31,23,59,00) if not end_dt   else end_dt
        self.period = period

        # instrument.get_collection_for_period(period)

        pass

    def run(self):
        """
        Runs the backtest and provides the results

        :rtype: TesterResult
        """

class TesterResult():
    """
    Backtest results
    """
    return_pct          = 0
    return_nominal      = 0
    max_drawdown_pct    = 0
    min_nominal         = 0

    def __init__(self, **kwargs):
        """

        """
        pass
