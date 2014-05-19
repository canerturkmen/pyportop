from datetime import timedelta
from django.db.models import *


class Instrument(Model):
    """
    Model encapsulates a single trading instrument (a.k.a security) in the POM system,
    in most of the anticipated cases a Forex trading pair
    """

    name        = CharField(null=False, max_length=10)
    description = CharField(null=True, default=None, max_length=150)
    is_forex    = BooleanField(null=False, default=True)

    def get_ccy1(self):
        """
        Get the 1st currency (CCY1) in the pair (i.e. base currency)

        :returns: ISO 4217 format currency pair name of CCY1
        """
        return self.name[:3]

    def get_ccy2(self):
        """
        Get the 2nd currency (CCY2) in the pair,

        :returns: ISO 4217 format currency pair name of CCY2
        """
        return self.name[3:7]

    def get_bar_collection(self, period):
        """
        Returns the set of bar objects that belong to a certain instrument, for a given periodicity

        :param period: the period for the data, if no data for this periodicity is available, no data will be returned
        :type period: model.models.Period

        :returns: an ordered list of IBar objects
        :rtype: list
        """
        return IBar.objects.filter(instrument=self, period=period).order_by("start_time").all()

    def get_bar_collection_timeframe(self, period, start, end):
        """
        Returns the set of bar objects that belong to a certain instrument, for a given periodicity, and between
        a given start and end time

        :param period: the periodicity for the date, if no data for this periodicity is available, no data will be returned
        :type period: model.models.Period
        :param start: the start datetime for the data
        :type start: datetime.datetime
        :param end: the end datetime for the data
        :type end: datetime.datetime

        :returns: an ordered list of IBar objects
        :rtype: list
        """
        return IBar.objects.filter(instrument=self, period=period, start_time__gte=start, start_time__lte=end)\
                                    .order_by("start_time").all()
        pass





class Period(Model):
    """
    Model for a timeframe object that is common to most financial security charts (e.g. H1, H4, M5)

    The naming convention is as follows: the first character of the `name` string is the time unit
    (`'M'` = minute, `'H'` = hour, `'D'` = day) and the rest of the string is the number of units for
    the timespan.
    """

    name = CharField(null=False, max_length=3)

    def get_numeric(self):
        """
        Get the number part of the period
        """
        try:
            return int(self.name[1:])
        except:
            return 0

    def get_unit_letter(self):
        """
        Get the first letter of the period(resolution) identifier (the unit)
        """
        return self.name[:1]

    def get_py_tdelta(self):
        """
        Get a pythonic ``timedelta`` object for the period implied by the number

        :returns: the timedelta object, None if the identifier is invalid
        :rtype: timedelta
        """
        get_unit = lambda x : {
                        "M": timedelta(minutes=1),
                        "H": timedelta(minutes=60),
                        "D": timedelta(days=1),
                        "W": timedelta(days=7)
                    }.get(x, None)

        numeric = self.get_numeric()

        # if the numeric part is not 0
        if numeric:
            return get_unit(self.get_unit_letter()) * numeric
        else:
            return None

    @classmethod
    def get_period(cls, pname):
        return cls.objects.get_or_create(name=pname)[0]

#
#class IBarCollection(Model):
#    """
#    Model that encapsulates a certain set of instrument data points (bars, `IBar`s)
#    """
#
#    instrument      = ForeignKey(to=Instrument, db_constraint=False)
#    period          = ForeignKey(to=Period)
#

class IBar(Model):
    """
    Model encapsulates a single timespan price data of an instrument in the POM system
    """

    start_time  = DateTimeField(auto_now=False, null=False)
    open        = FloatField(null=True)
    high        = FloatField(null=True)
    low         = FloatField(null=True)
    close       = FloatField(null=True)
    period      = ForeignKey(to=Period)
    instrument  = ForeignKey(to=Instrument)

    def get_avg_price(self):
        return (self.open + self.close) / 2