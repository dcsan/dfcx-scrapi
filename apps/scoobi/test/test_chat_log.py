'''
test setup
'''

import logging
from config.base_config import BaseConfig
from config.test_config import testConfig
import pandas as pd


# def test_write():
#     '''check we can find creds'''
#     sheet = Sheeter(testConfig, sheet_id=testConfig['sheets']['TestSheet'])
#     df = pd.read_csv('./test/test_data_input.csv')
#     sheet.write_tab(df, tabname='test_write')


# def test_read():
#     '''check we can find creds'''
#     sheet = Sheeter(testConfig, sheet_id=testConfig['sheets']['TestSheet'])
#     df = sheet.read_tab(tabname='test_read')
#     df.to_csv('./test/test_data_output.csv')
#     # logging.warning('df.names %s\n', df.names)
#     assert len(df) == 3, 'wrong length read'
#     # assert df['names'] == ['alpha', 'beta', 'charlie'], 'wrong names content'


# def test_write_named():
#     sheet = Sheeter(testConfig, sheet_id=testConfig['sheets']['TestSheet'])
#     sheet.write_tab(test_df, tabname='cars')
