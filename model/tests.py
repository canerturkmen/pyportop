from datetime import timedelta, datetime
import random
from django.utils.timezone import utc

__author__ = 'Caner'

from django.test import TestCase
from models import Instrument, Period, IBar

class InstrumentTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(InstrumentTest, self).__init__(*args, **kwargs)
        fill_dummy_data()
        self.inst = Instrument()
        self.inst.name = "EURUSD"
        self.inst.description = "Eur Usd pair"
        self.inst.is_forex = True

    def test_ccy1(self):
        self.failUnless(self.inst.get_ccy1() == "EUR")

    def test_ccy2(self):
        self.failUnless(self.inst.get_ccy2() == "USD")

    def test_bars(self):
        instrument = Instrument.objects.get(name="GBPUSD")
        list = instrument.get_bar_collection(Period.get_period("H1"))
        self.assertTrue(list) # only confirm a list is returned, tested manually = order working

    def test_bars_timeframe(self):
        instrument = Instrument.objects.get(name="GBPUSD")
        start = datetime.datetime(2014,05,03)
        end = datetime.datetime(2014,05,06,hour=23,minute=59, second=59)
        list = instrument.get_bar_collection_timeframe()
        self.assertTrue(list)
        for i in list:
            self.assertTrue(start <= i <= end)


class PeriodTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(PeriodTest, self).__init__(*args, **kwargs)

        self.h1period = Period(name="H1")
        self.m15period = Period(name="M15")

    def test_get_or_create(self):
        p = Period.get_period("M30")
        self.assertEqual(p.get_numeric(), 30)
        self.assertTrue(p.get_unit_letter() == "M") # TEST FAILING !
        self.assertEqual(p.get_py_tdelta(), timedelta(minutes=30))

    def test_get_numeric(self):
        self.assertTrue(self.h1period.get_numeric() == 1)
        self.assertTrue(self.m15period.get_numeric() == 15)

    def test_get_letter(self):
        self.assertTrue(self.h1period.get_unit_letter() == "H")
        self.assertTrue(self.m15period.get_unit_letter() == "M")

    def test_get_timedelta(self):
        h1tdelta = timedelta(hours=1)
        m15tdelta = timedelta(minutes=15)

        self.assertAlmostEquals(self.h1period.get_py_tdelta(), h1tdelta)
        self.assertAlmostEquals(self.m15period.get_py_tdelta(), m15tdelta)

def fill_dummy_data():
    p = Period(name="H1")
    p.save()

    i = Instrument(name="GBPUSD", description="The cable!", is_forex = True)
    i.save()

    price = 1.4567
    initial_date = datetime.datetime(2014,05,01,hour=12,minute=00,second=00, tzinfo=utc)
    for x in range(1000):
        tstamp = initial_date + (x * timedelta(hours=1))
        price += random.randint(1,3) * random.randint(-1,1) * random.randint(0, 10) / 1e4
        ibar = IBar(start_time = tstamp, open=price, high=price, low=price, close=price, period=p, instrument=i)
        ibar.save()

