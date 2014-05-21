import random
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
