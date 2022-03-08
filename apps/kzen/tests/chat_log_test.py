"""
testing real basic setup
"""
import logging
import re
from cxutils.digger.chat_log import ChatLog

from icecream import IceCreamDebugger
ic = IceCreamDebugger()

# import pandas as pd
# import numpy as np
# from cxutils.format.formatter import dumps

# from tests.testy import Testy

SAMPLE_LOG_FILE = 'tests/bill_sample_data.csv'


def xtest_import_chatlog():
    """import and process chatlog"""
    set_name = 'test_set'
    logs = ChatLog(set_name)
    logs.read_csv(SAMPLE_LOG_FILE)
    logs.set_meta({
        'xp_name': 'bill_test',
        'sprint': 99
    })
    assert len(logs.df) == 52
    logs.process()
    # logs.write_gdoc(tabname='test_set-v02')
    logs.write_bq()


def xtest_get_flow():
    row = {
        'transitions': "page(Default Start Flow::Start Page)|intent(Default Welcome Intent)|webhook(status=OK, latency=56)|page(Default Start Flow::Flow Transition)|condition(true)|page(Default Start Flow::HID DTMF AccType filter)"
    }
    trans = row['transitions']
    first: str = trans.split('|')[0]
    last: str = trans.split('|')[-1]
    assert "Default Start Flow" in first
    rex = r'page\((?P<flow>.*)::(?P<page>.*)\)'
    req = re.compile(rex)
    matched = req.match(first)
    logging.warning('matched %s', list(matched.groups()))
    assert len(matched.groups()) == 2
    assert matched.group('flow') == 'Default Start Flow'
    assert matched.group('page') == 'Start Page'


def test_get_transition_parts():
    row = {
        # 'transitions': "page(Default Start Flow::Start Page)|intent(Default Welcome Intent)|webhook(status=OK, latency=56)|page(Default Start Flow::Flow Transition)|condition(true)|page(Default Start Flow::HID DTMF AccType filter)"
        'transitions': 'page(Default Start Flow::HID DTMF AccType filter)|intent(head_intent.cannot_make_receive_call)|page(TRBL::Start Page)|page(TRBL::Tech Guru Check)|webhook(status=OK, latency=882)|condition($session.params.sessionMap.guruEligible = "N")|page(TRBL::Check Auth and Account Role)|condition($session.params.head = "cannot_make_receive_call" AND $session.params.isAuthenticated = "Y")|webhook(status=OK, latency=777)|page(TRBL::Confirm Calling Issue)'
    }
    parts = ChatLog.get_step_parts(row)
    assert parts['start']['flow'] == 'Default Start Flow'
    assert parts['start']['page'] == 'HID DTMF AccType filter'
    assert parts['end']['flow'] == 'TRBL'
    assert parts['end']['page'] == 'Confirm Calling Issue'
