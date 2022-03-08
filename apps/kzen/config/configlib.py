"""Handle loading a configs file
    skip=True items are not returned
"""

import logging
import re
from google.cloud.bigquery import table
import gspread
import pandas as pd
from icecream import ic
# import json


# from cxutils import logit
from cxutils import inout
from cxutils import biglib
from config import base_config

# import json
# CONFIG_PATH = 'public/runs/configs/agents.csv'
CREDS_BASE_PATH = './creds'
ic.configureOutput(prefix='configlib', includeContext=True)
# DO NOT import this as will create circ deps
# from cxutils.sheeter import Sheeter

# def default_creds_path():
#     '''return default creds'''
#     return './config/default-iam-creds.json'


def fetch_all_configs():
    """fetch from the kzen-configs into BigQuery"""
    results = []
    results.append(refresh_agent_configs())
    results.append(refresh_gdoc_configs())
    return results


def extract_agent_path(agent_url):
    """make an agent 'path' from the URL. core google lib calls this 'name' """
    # TODO - remove any trailing params
    return agent_url.replace("https://dialogflow.cloud.google.com/cx/", "")


def read_gdoc_tab(sheet_id, tab_name, creds_path=None):
    creds_path = creds_path or base_config.read('DEFAULT_CREDS_PATH')
    try:
        gsp = gspread.service_account(filename=creds_path)
        gdoc = gsp.open_by_key(sheet_id)
        tab = gdoc.worksheet(tab_name)
        data = tab.get_all_records()
    except gspread.exceptions.APIError as err:
        logging.error('gspread API exception \nsheet_id: [%s] tab_name: [%s] \ncreds_path: [%s]',
                      sheet_id, tab_name, creds_path)
        raise err

    logging.info('gspread tab:%s len:%s', tab_name, len(data))
    df = pd.DataFrame(data[1:], columns=data[0])
    return df


def refresh_agent_configs():
    """fetch agent configs from gsheet"""
    config_sheet = base_config.read('kzen_config_doc')

    df = read_gdoc_tab(sheet_id=config_sheet, tab_name='agents')

    print('got agents', len(df))

    for _index, row in df.iterrows():
        agent_path, agent_url = row['agent_path'], row['agent_url']
        if not agent_path and agent_url:
            agent_path = extract_agent_path(agent_url)
            row['agent_path'] = agent_path  # does this update original

        if not row['agent_path']:
            logging.error('cannot find agent_path and no url %s', row)

        # df.loc[index] = row

    # TODO coerce fields eg TRUE/FALSE for skip
    ic('fetch agents OK:\n %s', len(df))
    # ic('fetch agents OK:\n %s', df.filter(
    #     items=['cname', 'agent_path']))
    biglib.insert_df(df, table_name='agents', if_exists='replace')

    return {
        'agent_configs': len(df),
        # 'df': df
    }
    # fpath = CONFIG_PATH
    # df.to_csv(fpath, index=False)
    # ic('fetched agent to %s', fpath)


def refresh_gdoc_configs():
    """fetch all configs from a google sheet
        we dont do this often, just when a new sheet is added to ecosystem
        so we can refer to configs by the cname elsewhere
    """
    config_sheet = base_config.read('kzen_config_doc')
    df = read_gdoc_tab(sheet_id=config_sheet, tab_name='gdocs')
    df['sheet_id'] = None
    for index, row in df.iterrows():
        row['sheet_id'] = split_sheet_id(row)
        df.loc[index] = row

    # ic('configs', df)
    # ic('config', df.head().transpose())
    # ic('parts', df['cname'], df['sheet_id'])

    # print('gdocs', df)
    biglib.insert_df(df, table_name='gdocs', if_exists='replace')
    ic('fetch gdocs OK:', len(df))
    return {
        'gdoc_configs': len(df),
        # 'cnames': df['cname']
    }


def split_sheet_id(row):
    """extract sheet_id from URL"""
    # strip off any /edit?etc in the URL and then take the bit after /d/ ie: /d/(.*)
    url = row['url']

    if not url:
        msg = f'failed to get URL for sheet {row}'
        logging.error(msg)
        raise KeyError(msg)

    clean = re.sub("/edit.*", "", url)
    if clean != url:
        logging.warning(
            'check for bad URLs - remove all /edit? strings: \nbefore: %s \n after: %s', url, clean)
    parts = clean.split('/')
    sheet_id = parts.pop()
    if len(sheet_id) != 44:
        # may have to change this if sheet_id length changes in future
        msg = f'failed to get sheet_id {sheet_id}'
        logging.error(
            'failed to get sheet_id [%s] \nfrom url [%s]', sheet_id, url)
        raise ValueError(msg)
    return sheet_id


def get_agent(cname):
    """get info on agent from BQ"""
    tid = biglib.make_table_id('agents')
    qstring = f'select * from {tid} where cname="{cname}"'
    row = biglib.query_one(qstring)
    if not row:
        msg = f'cannot get agent for {cname}'
        logging.error(msg)
        raise Exception(msg)
    else:
        ic('get_agent cname:%s', cname)
        logging.debug('get_agent cname:%s  agent=> %s', cname, row)
    return row


def get_gdoc_info(cname):
    """get info on a named gdoc from BQ"""
    table_id = biglib.make_table_id('gdocs')
    query = f'select * from {table_id} where cname="{cname}" limit 1'
    rows = biglib.query_list(query)
    if len(rows) < 1:
        msg = f'cannot find gdoc cname=[{cname}]'
        gdocs = fetch_all_gdocs()
        df = pd.DataFrame(gdocs)
        logging.error(
            'cannot find doc cname: [%s] gdocs \n%s', cname, df['cname'])
        raise KeyError(msg)

    doc = rows[0]
    return doc


def fetch_all_gdocs():
    table_id = biglib.make_table_id('gdocs')
    query = f'select * from {table_id} '
    rows = biglib.query_list(query)
    return rows


def reform(rows, form):
    """web needs dict not json to prevent double wrapping
    params:
        rows: BQ query result
    """
    if form == 'json':
        return biglib.to_json(rows)
    elif form == 'dict':
        return biglib.to_dict(rows)

    # else
    return rows


def get_agents(form='bq'):
    """read configs from BQ
    params:
        form: bq or json
    """
    tid = biglib.make_table_id('agents')
    qstring = f'select * from {tid}'
    rows = biglib.query(qstring)
    ic('agents %s', rows)
    return reform(rows, form)


def get_gdocs(form='bq'):
    """return all gdocs"""
    tid = biglib.make_table_id('gdocs')
    qstring = f'select * from {tid}'
    rows = biglib.query(qstring)
    ic('gdocs %s', rows)
    return reform(rows, form)

# def get_configs(defaults=None, agent_name=None, limit=False):
#     '''load from a JSON config file'''
#     defaults = defaults or {}
#     configs = read_config_file()
#     # with open(CONFIG_PATH) as fp:
#     #     configs = json.load(fp)
#     configs = [c for c in configs if c.get('skip') is not "TRUE"]

#     if agent_name:
#         configs = [c for c in configs if c.get('agent_name') == agent_name]

#     if len(configs) < 1:
#         logging.error('cannot find agent_name %s', agent_name)

#     if limit:
#         configs = configs[:limit] # just a sample

#     for config in configs:
#         config.update(defaults)
#         agent_path = config['agent_path']
#         config['agent_url'] = f'https://dialogflow.cloud.google.com/cx/{agent_path}'
#         config['agent_id'] = agent_path.split('/')[-1]

#         config["creds_file"] = config.get('creds_file') or 'dc-YOUR-GCP-PROJECT.json'
#         config['creds_path'] = f'{CREDS_BASE_PATH}/{config["creds_file"]}'
#         # print('added agent_id', config)
#     return configs


# def get_one(defaults=None, agent_name=None):
#     '''get a single config by name or else first one

#     args:
#         agent_name: name of the agent you want to filter for
#     returns:
#         config - an agent json config
#     '''
#     configs = get_configs(defaults, agent_name)
#     if not configs:
#         logging.error("Cannot find agent %s", agent_name)
#     return configs.pop(0) # first elem
