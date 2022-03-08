"""testing tuner"""

# import logging

# from cxutils.format.formatter import dumps
from cxutils.tuner.tuner import Tuner

# TODO - create a test set just for testing!
SET_NAME = 'BILL-coreset'


def test_sankey():
    """get sims values formatted for a sankey"""
    set_name = SET_NAME
    tuner = Tuner(set_name)
    stats = tuner.get_sankey()
    assert len(stats) > 3
    # logging.warning('stats \n%s', dumps(stats))


def test_simset():
    """a simset for a left intent"""
    set_name = 'BILL-coreset'
    left = 'L.bill_view_current'
    tuner = Tuner(set_name=set_name)
    sims = tuner.get_simset(left)
    assert len(sims) > 3
    # logging.warning('sims %s', dumps(sims[0:3]))
