'''
test setup
'''

from config.base_config import BaseConfig
from lib.data.biglib import BigLib

# setup your credentials and then import and select them
from config.client_config import clientConfig
testConfig = clientConfig


def test_creds():
    '''check we can find creds'''
    cpath = testConfig['creds_path']
    assert testConfig['creds_path'] is not None
    fp = open(cpath, "r")


def test_db_access():
    '''check we can access feedback_annotations BQ table'''
    BigLib.configure(testConfig)
    table = 'fbl_raw'
    table_id = BigLib.make_table_id(table)
    qs = f'select * from {table_id} limit 10'
    df = BigLib.query_df(qs)
    assert(len(df)) == 10
