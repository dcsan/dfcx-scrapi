"""
    wrapper and helped functions for BigQuery API

    namespacing is:
        gcp-project.dataset.table

    actual GCP project / table names etc are contained in the config/app_config.json which is read via base_config

"""

# from sys import stdout
# from datetime import datetime
import time
import logging
import json

import pandas as pd
import pandas_gbq
from icecream import IceCreamDebugger


# from typing import List, Set, Dict, Tuple, Optional

# write to BT
from google.oauth2 import service_account
from google.cloud import bigquery
from requests.exceptions import InvalidSchema
from cxutils import logit
from cxutils.format.formatter import dumps
from config import base_config

ic = IceCreamDebugger(prefix='biglib|\t')

bq_creds = service_account.Credentials.from_service_account_file(
    base_config.read('DEFAULT_CREDS_PATH'))

pandas_gbq.context.credentials = bq_creds

bq_client = bigquery.Client(credentials=bq_creds, project=bq_creds.project_id)

# FIXME _ duplication
RUNS_TABLE = base_config.read('RUNS_TABLE')
BQ_DATASET = base_config.read('BQ_DATASET')

SLOW_QUERY_TIME = 1.5

logger = logging


def load_csv(fp=None):
    """load a csv file from fs"""
    fp = fp or 'cases/silver-set/results/intent-runs.csv'
    df = pd.read_csv(fp)
    return df


def query(qstring, _get_all=True):
    """run a time query string"""
    start = time.time()
    logger.info('query>> %s', qstring)
    try:
        job = bq_client.query(qstring)
        result = job.result()
    except Exception as err:
        logging.error('failed BQ job %s', err)
        raise err
    end = time.time()
    duration = end - start
    if duration > SLOW_QUERY_TIME:
        logger.info('slow query %s done in %i s', qstring, duration)

    # if getall:
    #     result = get_all(result, job)
    # logger.info('result rows: [%s]', result.total_rows)
    return result


def get_all(cursor, job):
    """unwind the bq data"""
    destination = job.destination
    destination = bq_client.get_table(destination)

    # Download rows.
    # The client library automatically handles pagination.
    rows = bq_client.list_rows(destination, max_results=15000)
    data = []
    for row in rows:
        data.append(row)
        # print("name={}, count={}".format(row["name"], row["total_people"]))
    logging.info('get_all rows: %s', len(data))
    return data


def query_df(qstring):
    """return results as dataframe"""
    cursor = query(qstring)
    df = cursor.to_dataframe()
    logging.info('query df len %s', len(df))
    return df


def query_list(qstring):
    """return a list of items"""
    logging.info('qstring: %s', qstring)
    query_job = bq_client.query(qstring)
    data = [dict(row) for row in query_job]
    # logging.info('query %s => rows: %s', qstring, len(data))
    return data


def query_one(qstring):
    """expect just a single result"""
    # get first result
    rows = query(qstring)
    logging.debug('query_one rows: %s', rows)  # an 'object' thanks
    # get first row since its not a real iterator
    try:
        row = next(x for x in rows)
        blob = dict(row)
    except StopIteration as err:
        logging.error('StopIteration Error at query_one %s', err)
        logging.error('qstring: %s', qstring)
        return None
    logging.debug('query_one result: %s', blob)
    return blob


def make_table_id(table_name):
    """return fully qualified table_id"""
    tid = f'{BQ_DATASET}.{table_name}'
    # print('tid', tid)
    return tid


def enforce_schema(df, table):
    """filter a dataframe for only fields that exist in the BQ table"""
    # TODO - check no duplicate or empty columns
    # as this causes
    fields = [field.name for field in table.schema]
    schema_json = [
        {
            'name': schema.name,
            'type': schema.field_type
        } for schema in table.schema
    ]
    logging.info('filter on fields %s', fields)
    try:
        sub = df.filter(fields)
    except ValueError as err:
        logging.error(
            'failed to check schema - check for empty/duplicate columns')
        raise(err)

    set1 = set(df.columns)
    set2 = set(sub.columns)
    diff = set1 - set2
    if diff:
        logging.warning('extra   fields %s', set1 - set2)
        logging.warning('missing fields %s', set2 - set1)

    # logging.info('df.columns %s', columns)
    # logging.info('bq.fields %s', fields)
    # logging.info('schema_json %s', schema_json)
    # logging.info('sub %s', sub.head())
    # logging.info('sub.shape %s', sub.shape)

    return sub, schema_json


def dump_schema(table_name=None, table_id=None):
    """export schema
    args:
        at least one of
        table_id
        table_name
    """
    table_id = table_id or make_table_id(table_name)
    table = bq_client.get_table(table_id)
    dump = ""
    for field in table.schema:
        dump += str(field) + "\n"
    logging.info('\nschema dump for table: %s \n%s', table_id, dump)
    fpath = f'config/schema/{table_name}.txt'
    with open(fpath, 'w') as fhandle:
        fhandle.write(dump)


def dump_all_schemas():
    """dump all tables"""
    table_names = base_config.read('BQ_TABLES')
    for one_table in table_names:
        dump_schema(one_table)


def insert_df(df, table_name=None, table_id=None, if_exists='append'):
    """insert a dataframe into a table"""

    if (len(df) < 1):
        logging.warning('ERROR tried to insert empty dataframe %s', table_name)

    cols = df.columns
    df = df.loc[:, ~df.columns.duplicated()]
    if len(cols) != len(df.columns):
        logging.error('DF had duplicate columns: \n%s', dumps(cols))

    # remove duplicates in the index
    rowcount = len(df)
    df[df.index.duplicated()]
    if len(df) != rowcount:
        logging.error('df had duplicates in the index')

    table_id = table_id or make_table_id(table_name)
    table = bq_client.get_table(table_id)
    df, schema_json = enforce_schema(df, table)

    try:
        res = df.to_gbq(
            destination_table=table_id,
            project_id=base_config.read('BQ_PROJECT'),
            if_exists=if_exists,
            table_schema=schema_json
        )
        logging.info('inserted into %s df len %s res:\n %s',
                     table_id, len(df), res)
    # except google.api_core.exceptions.BadRequest as err:
    except BaseException as err:
        logging.error(
            'failed to insert\ntable_name: %s | table_id: %s', table_name, table_id)
        logging.info('table_schema: %s', schema_json)
        logging.info('columns %s', cols)
        print('df.head(5): ')
        print(df.head(5))
        logging.error(err)


def select_from(selection='*', where=None, table_id=None, table_name=None, limit=None, order=None):
    """format a query with BQ wrapper flab"""
    table_id = table_id or make_table_id(table_name)
    qstring = f"select {selection} from {table_id}"
    if where:
        qstring += f" where {where}"
    if order:
        qstring += f" order by {order} "
    if limit:
        qstring += f" limit {limit}"
    cursor = query(qstring)
    return cursor
    # yield from cursor


def get_df(selection='*', where=None, table_id=None, table_name=None, limit=None, order=None):
    """return orm query as df"""
    table_id = table_id or make_table_id(table_name)
    cursor = select_from(selection=selection, where=where,
                         table_id=table_id, limit=limit, order=order)
    return cursor.to_dataframe()


def delete(where=None, table_id=None, table_name=None):
    """delete from table"""
    table_id = table_id or make_table_id(table_name)
    if not where:
        logging.error('tried to delete with WHERE %s', table_id)
        return None
    qstring = f' delete from `{table_id}` WHERE {where}'
    ic('BQ delete:', qstring)
    return query(qstring)


def to_json(cursor):
    """convert bq cursor to json"""
    records = [dict(row) for row in cursor]
    blob = json.dumps(str(records))
    return blob


def to_dict(cursor):
    """convert bq cursor to json"""
    records = [dict(row) for row in cursor]
    return records


def add_uuids(table_name=None):
    """generate uuid s for a table"""
    table_id = make_table_id(table_name)
    qstring = f"""
    update {table_id}
    set uuid = generate_uuid()
    where true;
    """
    query(qstring)


def fix_timestamp(ts: str):
    # When you load JSON or CSV data, values in TIMESTAMP columns
    # must use a dash (-) separator for the date portion of the timestamp,
    # and the date must be in the following format:
    # YYYY-MM-DD (year-month-day).
    # The hh:mm:ss (hour-minute-second) portion of the timestamp must use a colon (:) separator.
    # 5/26/2021 19:13:00 => 2021-05-26 19:13:00
    # NEW FORMAT! Looker breaks them in a different way lol
    # 2021-07-07 0:31:04  (note only one digit for the hour)

    try:
        date_part, time_part = ts.split(' ')
    except ValueError as _err:
        logging.error('failed to convert ts [%s]', ts)
        return None

    if '-' in date_part:
        # dangerous log if applying to a huge table...
        # logging.warning('date already fixed? %s', ts)
        year, month, day = date_part.split('-')  # 2021-07-07
        # return ts
    else:
        month, day, year = date_part.split('/')  # 5/26/2021

    # if not month:
    day = day.zfill(2)
    month = month.zfill(2)
    year = year.zfill(4)

    try:
        hour, minute, seconds = time_part.split(':')
    except ValueError:
        # some stamps with no seconds, sigh
        hour, minute = time_part.split(':')
        seconds = '00'

    hour = hour.zfill(2)
    minute = minute.zfill(2)
    seconds = seconds.zfill(2)

    if len(time_part) == 5:
        time_part = f'{time_part}:00'  # append seconds
    bq_date = f'{year}-{month}-{day} {hour}:{minute}:{seconds}'
    if len(bq_date) < 19:
        # TODO fix goddam timestamps again
        print('date', bq_date)
        return None
    return bq_date


def runs_table_path():
    """we just need the table path without the GCP project for some APIs"""
    # eg 'YOUR-BQ-DATASET.runs'
    dataset = base_config.read('BQ_DATASET')
    table_name = base_config.read('BQ_RUNS_TABLE_NAME')
    tpath = f"{dataset}.{table_name}"
    return tpath


def save_run(df):
    """save a benchmark run results and enforce schema"""

    # dataframe format
    runs_schema_df = {
        'created_at':  'datetime64[ns]',
        'run_id': 'int',
        'agent': 'str',
        'text': 'str',
        'expect': 'str',
        'actual': 'str',
        'expect_hit': 'bool',
        'actual_hit': 'bool',
        'score': 'float',
        'pf': 'bool',
        'hit': 'int',
        'active': 'bool',
        'tags': 'string'
    }

    # bq format
    runs_schema_bq = [
        {'name': 'created_at', 'type': 'TIMESTAMP'},
        {'name': 'run_id', 'type': 'INTEGER'},
        {'name': 'agent', 'type': 'STRING'},
        {'name': 'text', 'type': 'STRING'},
        {'name': 'expect', 'type': 'STRING'},
        {'name': 'actual', 'type': 'STRING'},
        {'name': 'expect_hit', 'type': 'BOOLEAN'},
        {'name': 'actual_hit', 'type': 'BOOLEAN'},
        {'name': 'score', 'type': 'FLOAT'},
        {'name': 'rank', 'type': 'INTEGER'},
        {'name': 'pf', 'type': 'BOOLEAN'},
        {'name': 'hit', 'type': 'INTEGER'},
        {'name': 'active', 'type': 'BOOLEAN'},
        {'name': 'tags', 'type': 'STRING'},
    ]

    logger.debug('save_run\n')
    logger.debug(df.head(1))
    try:
        df = df.astype(runs_schema_df)
    except ValueError as err:
        logging.warning('err converting BQ table \n%s', err)
        print(df.head(100))
        raise(err)

    try:
        df.to_gbq(
            destination_table=runs_table_path(),
            project_id=base_config.read('BQ_PROJECT'),
            if_exists='append',
            table_schema=runs_schema_bq,
        )
        logger.debug(f'wrote {len(df)} lines to bgq')
    except pandas_gbq.gbq.InvalidSchema as err:
        logging.error('invalid schmema for df \n%s', df.columns)
        raise(err)


def get_runs(limit=False):
    """get runs"""
    qstring = f"SELECT * FROM {RUNS_TABLE}"
    if limit:
        qstring += f"LIMIT {limit}"
    return query(qstring)


def get_run_ids(_limit=False):
    """get all run_id """
    qstring = f"SELECT distinct(run_id) FROM {RUNS_TABLE}"
    return query(qstring)


def count_run_items():
    """count run items"""
    qstring = f"""
    select
        agent,
        count(run_id) as count,
        run_id as run_id
    from {RUNS_TABLE}
    group by run_id, agent
    """
    done = query(qstring)
    return done  # bigquery result
    # df = res.to_dataframe()
    # return df


def remove_run(agent=None, run_id=None):
    """delete a run"""
    if agent:
        qstring = f'''delete from {RUNS_TABLE} where agent = "{agent}" '''
    if run_id:
        qstring = f'''delete from {RUNS_TABLE} where run_id = "{run_id}" '''
    logger.warning('removing runs: %s', agent)
    return query(qstring)


def rename(agent=None, new_name='newname'):
    """rename agent"""
    qstring = f'''
        update {RUNS_TABLE}
        set agent = "{new_name}"
        where agent = "{agent}"
    '''
    return query(qstring)


def set_tags(agent=None, tags='tags'):
    """write tags to table"""
    if agent:
        qstring = f'''
            update {RUNS_TABLE}
            set tags = "{tags}"
            where agent = "{agent}"
        '''
    else:
        qstring = f'''
            update {RUNS_TABLE}
            set tags = "{tags}"
            where TRUE
        '''

    return query(qstring)


def set_active(agent=None, active=False):
    """set active flag for display in dashboard"""
    if agent:
        qstring = f'''
            update {RUNS_TABLE}
            set active={active}
            where agent = "{agent}"
        '''
    else:  # all
        qstring = f'''
            update {RUNS_TABLE}
            set active={active}
            where TRUE
        '''
    return query(qstring)


def clean_small_runs(limit=100):
    """remove all runs < limit items eg tests"""
    items = count_run_items()
    for run in items:
        # print(f'consider run {dict(run)}')
        if run.count < limit:
            logger.info(f'delete run {dict(run)}')
            remove_run(run_id=run.run_id)


def load_run(agent=None):
    """load all data from a test run"""
    qstring = f'''select * from {RUNS_TABLE} where agent="{agent}" '''
    data = query(qstring)
    df = data.to_dataframe()
    logit.head(df)
    # agent = df['agent'][0]
    row = df.iloc[0]
    print('row', row)
    print('row', row.agent)
    return df


def run_stats():
    """show stats"""
    # delete_run(1612161694)
    # clean_small_runs()
    logit.head(count_run_items(), 500)


def load_gs(uri, table_id):
    """load csv from google storage"""
    job_config = bigquery.LoadJobConfig(
        # schema=[
        #     bigquery.SchemaField("name", "STRING"),
        #     bigquery.SchemaField("post_abbr", "STRING"),
        # ],
        skip_leading_rows=1,
        # The source format defaults to CSV, so the line below is optional.
        source_format=bigquery.SourceFormat.CSV,
    )
    load_job = bq_client.load_table_from_uri(
        uri,
        table_id,
        job_config=job_config
    )  # Make an API request.

    load_job.result()  # Waits for the job to complete.

    destination_table = bq_client.get_table(table_id)  # Make an API request.
    print("Loaded {} rows.".format(destination_table.num_rows))
