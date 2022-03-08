'''
exporting the details of a flow
'''

import json
# from sys import stdout
import datetime
import logging

import pandas as pd
import pandas_gbq


# write to BT
from google.oauth2 import service_account
from google.cloud import bigquery
# from cxutils import logit

from cxutils import biglib
# from models import bq_utils

# from config import configlib
from config import base_config

# named tables
DEFAULT_CREDS = base_config.read('DEFAULT_CREDS_PATH')
BQ_PROJECT = base_config.read('BQ_PROJECT')
FLOWSTATS_TABLE = base_config.read('FLOWSTATS_TABLE')

bq_creds = service_account.Credentials.from_service_account_file(DEFAULT_CREDS)
pandas_gbq.context.credentials = bq_creds
bq_client = bigquery.Client(credentials=bq_creds, project=bq_creds.project_id)


# TODO - move to biglib

def check_schema(df):
    '''compare the BQ schema with a DF structure to find problems'''
    # bq_schema = pandas_gbq.schema.generate_bq_schema(df)
    df_schema = pd.io.json.build_table_schema(df)
    table = bq_client.get_table(FLOWSTATS_TABLE)  # Make an API request.
    remote_schema = table.schema
    df_fields = df_schema['fields']
    # schema = bq_utils.generate_bq_schema(df)
    # logit.obj('bq_schema', bq_schema['fields'])
    # logit.obj('df_schema', df_schema)
    # logit.obj('remote_schema', remote_schema)

    check = {
        'ok': True,
        'missing': [],
        'mismatch': []
    }

    bq_fields = {}
    df_fields = {}
    # convert fields to a dict format
    for item in remote_schema:
        bq_fields[item.name] = item.field_type.lower()
    for item in df_schema['fields']:
        df_fields[item['name']] = item['type'].lower()
    df_fields.pop('index') # ignore index which is DF only thing

    # just get EXTRA fields in the df
    for k in df_fields:
        bqtype = bq_fields.get(k)
        # find missing fields
        if not bqtype:
            check['ok'] = False
            check['missing'].append(k)
            # continue
        dftype = df_fields.get(k)
        if bqtype != dftype:
            if dftype == 'datetime' and bqtype == 'timestamp':
                continue # these are equivalent
            # else:
            check['ok'] = False
            check['mismatch'].append(f'key [{k}] df= {dftype} bq= {bqtype}')
    if check['ok'] is not True:
        logging.warning('schema mismatch %s', json.dumps(check, indent=2))


def save_stat(df, stat, _stats_config):
    '''save one stat to bigquery db'''
    df['timestamp'] = datetime.datetime.now()
    df['latest'] = True
    check_schema(df)
    agent = stat['agent_name']

    # if stats_config['if_exists'] == 'replace':
    #     qstring = f'''delete from {FLOWSTATS_TABLE} where agent = "{agent}" '''
    #     biglib.query(qstring)

    qstring = f'''
        update {FLOWSTATS_TABLE}
        set latest = False
        where agent = "{agent}"  
    '''
    biglib.query(qstring)

    df.to_gbq(
        destination_table=FLOWSTATS_TABLE,
        project_id=BQ_PROJECT,
        if_exists='append',
        # table_schema=bq_schema,
    )
    logging.debug('wrote %s lines to bgq', len(df))
