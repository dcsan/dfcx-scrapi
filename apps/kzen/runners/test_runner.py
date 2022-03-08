"""
runner for CUSTOMER project
"""
import logging
from icecream import IceCreamDebugger

from config import configlib

from cxutils.testrunner.testrunner import TestRunner

ic = IceCreamDebugger(
    prefix='testrunner'
)


def testone(tabname, sheet_key=None, _cached=False):
    """run a single named tab sheet of tests"""
    logging.info('testone=> tabname: %s | sheet_key: %s', tabname, sheet_key)
    options = {
        'sheet_key': sheet_key
    }
    tester = TestRunner(options)
    msg = tester.run_one_tab(tabname, sheet_key)
    return msg


def run():
    """lets do it"""
    ic('main')

    configlib.refresh_gdoc_configs()
    configlib.refresh_agent_configs()

    testone('XP-meena', sheet_key='xp_tests')  # one named tab
