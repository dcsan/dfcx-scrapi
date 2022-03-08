"""
testing real basic setup
"""

from cxutils.digger.chat_log import ChatLog
from cxutils.digger.chat_static import ChatStatic
import pandas as pd
import numpy as np
import logging
from cxutils.format.formatter import dumps

# from cxutils import biglib
test_log_data = [
    {'session': 'a', 'intent': "no-match"},
    {
        'utterance': 'show me current bill',
        'session': 'a', 'intent': "head_intent.bill_view_current"},
    {'session': 'a', },

    {'session': 'b', 'intent': "no-match"},
    {'session': 'b', 'intent': "yes-me"},
    {'session': 'b', },
]

# data = [
#     {
#         'intent': None,
#         'val': -1
#     },
#     {
#         # 'intent': 'not-me',  no intent field
#         'val': 0
#     },

#     {
#         'intent': 'not-me',
#         'val': 0
#     },
#     {
#         'intent': 'yes-me',
#         'val': 1
#     },
#     {
#         'intent': 'dont-test-me',
#         'val': 3
#     },
#     {
#         'intent': 'three'
#     }

# ]


def show(msg, df):
    """has to be warning to show during tests"""
    logging.warning('\n\n--- %s\n%s', msg, df)


def find_first(df, matches=None):
    matches = ChatStatic.intent_drivers
    for _index, item in df.iterrows():
        # show('item', item)
        if item['intent'] in matches:
            return item['intent']


def x_test_find_first():
    """finding the first 'driver' from curated list"""
    df = pd.DataFrame(test_log_data)
    df['driver'] = 'before'
    sessions = df.groupby('session')
    for _session_id, convo in sessions:
        driver = find_first(convo)
        df.loc[df['session'] == _session_id, 'driver'] = driver

    picked = df[df['driver'] == 'head_intent.bill_view_current']
    assert len(picked) == 3

    show('df', df)


# def x_test_calc_driver():
#     """calculate the driver"""
#     set_name = 'test_set'
#     chat_logs = ChatLog(set_name)
#     chat_logs.from_dict(test_log_data)
#     stats = ConvoStat(set_name)
#     stats.chat_logs = chat_logs
#     assert len(stats.chat_logs.df) == 6
#     lines, convos = stats.process()
#     picked = lines[lines['driver'] == 'head_intent.bill_view_current']
#     assert len(picked) == 3
#     assert len(convos) == 2

#     show('lines', lines)
#     show('len convos', len(convos))
#     for idx, convo in convos:
#         show('convo:' + idx, convo)
