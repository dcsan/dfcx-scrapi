'''
short logging util to print objects and colors
'''

import json
import logging
from sys import stdout
from typing import Dict, Union

import pandas as pd
from google.cloud import bigquery

import ansimarkup

# TODO - allow pass in a 'where' param and make class with constructor

logging.basicConfig(
    format='\n[dfcx/%(module)s] %(levelname)s | %(message)s',
    datefmt='',
    level=logging.INFO,
    # force=True
)


handler = logging.StreamHandler(stdout)
# formatter = logging.Formatter(f'[{name}] %(message)s')
formatter = logging.Formatter(f'%(message)s')
handler.setFormatter(formatter)


# class Logit:
#     '''wrap the logging to suppress timecodes'''

#     def __init__(self, name):
#         self.name = name
#         # name = name or __name__
#         print(f'create logger {name}')
#         # logging.info('creating logger for %s', name)
#         _logger = logging.getLogger(name)
#         if _logger.hasHandlers():
#             print('already handlers')
#         else:
#             print('adding handlers')
#         # if not _logger.hasHandlers():
#         _logger.addHandler(handler)
#         _logger.propagate = False
#         # print(f'logger {name} had handlers')
#         self.logger = _logger
#         self.logger.info('fuck you')

#     def info(self, *args, **kwargs):
#         '''pass through'''
#         self.logger.info(*args, **kwargs)

#     def debug(self, *args, **kwargs):
#         '''pass through'''
#         self.logger.debug(*args, **kwargs)


# logger = Logit('logit')

logger = logging


def obj(msg, blob):
    '''
    print json object with colored message
    fallback to print if the JSON doesnt parse
    '''
    try:
        msg = ansimarkup.parse(msg)
        logger.info('%s =>\n%s', msg, json.dumps(blob, indent=2))
    except:
        print(msg, obj)


def info(msg):
    '''simple colored log'''
    msg = ansimarkup.parse(msg)
    logger.info(msg)


def head(data: Union[Dict, pd.DataFrame], limit=20, msg=None):
    '''
    try a few ways to print the first line
    of dataframe, bigquery result or plain dict
    '''
    # print('data is a ', type(data))
    if isinstance(data, dict):
        df = pd.DataFrame(data)
    elif isinstance(data, bigquery.table.RowIterator):
        # print('data was', data)
        # data = list(data)
        # print('data is', data)
        df = data.to_dataframe()
        # df = pd.DataFrame.from_dict(data)
    else:
        df = data

    if msg:
        print(msg)
    print(df.head(limit))
    if len(df) > limit:
        print(f"cut at {limit} of {len(df)} total")
