from datetime import timedelta
from django.db.models import *


class Instrument(Model):
    """
    Model encapsulates a single trading instrument (a.k.a security) in the POM system,
    in most of the anticipated cases a Forex trading pair.

    The model includes the following attributes:

    - *name* ``CharField``          The name of the instrument in ISO4217 pair names
    - *description* ``CharField``   The description, if any, for the instrument
    - *is_forex* ``BooleanField``   Currently unused
    """

    name        = CharField(null=False, max_length=10)
    description = CharField(null=True, default=None, max_length=150)
    is_forex    = BooleanField(null=False, default=True)

    def get_ccy1(self):
        """
        Get the 1st currency (CCY1) in the pair (i.e. base currency)

        :returns: ISO 4217 format currency pair name of CCY1
        :rtype: str
        """
        return self.name[:3]

    def get_ccy2(self):
        """
        Get the 2nd currency (CCY2) in the pair,

        :returns: ISO 4217 format currency pair name of CCY2
        :rtype: str
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

    @classmethod
    def get_instrument(cls, inst):
        """
        Class method for retrieving an Instrument instantiation (persisted) by providing the name

        :param inst: the name for the instrument
        :type inst: str

        :returns: the Instrument object (if any)
        :rtype: Instrument
        """
        return cls.objects.get(name=inst)




class Period(Model):
    """
    Model for a timeframe object that is common to most financial security charts (e.g. H1, H4, M5)

    The naming convention is as follows: the first character of the `name` string is the time unit
    (``'M'`` = minute, ``'H'`` = hour, ``'D'`` = day) and the rest of the string is the number of units for
    the timespan.

    The only attribute of the class is as follows:

    - *name*   ``CharField``: the name of the period, in the manner explained above
    """

    name = CharField(null=False, max_length=3)

    def get_numeric(self):
        """
        Get the number part of the period

        :returns: the numeric part of the field
        :rtype: int
        """
        try:
            return int(self.name[1:])
        except:
            return 0

    def get_unit_letter(self):
        """
        Get the first letter of the period(resolution) identifier (the unit)

        :returns: the letter part of the period name
        :rtype: str
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
        """
        Class method for retrieving a ``Period`` object (persisted) by providing the name.

        :param pname: the period name in the naming convention explained in the class documentation
        :type pname: str

        :returns: the Period object
        :rtype: Period
        """
        return cls.objects.get_or_create(name=pname)[0]


class IBar(Model):
    """
    Model encapsulates a single timespan price data of an instrument in the POM system.

    Attributes of the object are as follows:

    - *start_time*      ``DateTimeField``   The start date time of the timespan implied by the ``IBar`` object
    - *open*            ``FloatField``      The opening price of the instrument in the timespan
    - *high*            ``FloatField``      The highest price of the instrument in the timespan
    - *low*             ``FloatField``      The lowest price of the instrument in the timespan
    - *close*           ``FloatField``      The closing price of the instrument in the timespan
    - *period*          ``ForeignKey``      Reference to the ``Period`` object
    - *instrument*      ``ForeignKey``      Reference to the ``Instrument`` object

    """

    start_time  = DateTimeField(auto_now=False, null=False)
    open        = FloatField(null=True)
    high        = FloatField(null=True)
    low         = FloatField(null=True)
    close       = FloatField(null=True)
    period      = ForeignKey(to=Period)
    instrument  = ForeignKey(to=Instrument)

    def get_avg_price(self):
        """
        Get the average price implied by the ``IBar`` object, calculated as the average of opening and closing prices

        :returns: the average price of the bar
        :rtype: float
        """
        return (self.open + self.close) / 2


