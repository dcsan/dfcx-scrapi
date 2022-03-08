'''making basic flowstats about each agent'''

from cxutils.sapiwrap.mega_agent import MegaAgent

from config import configlib
from cxutils import logit
import time

import pandas as pd

from models import flowstats

"""
    calculate basic stats on agents
    a daily runner to check we don't go over the current quota
    of 20 flows per agent
"""


def get_sapi(config):
    '''load sapi instance'''
    # TODO - fix paths
    creds_path = f'./creds/{config["creds_file"]}'
    sapi = MegaAgent(
        creds_path=creds_path,
        agent_path=config['agent_path']
    )
    return sapi


def get_stats():
    '''get basic stats on an agent: number of flows etc'''
    stats_config = {
        'if_exists': 'replace'
    }
    configs = configlib.get_configs()
    stats = []
    for config in configs:
        sapi = get_sapi(config)
        agent_id = config['agent_path']
        agent = sapi.get_agent(agent_id)
        print('agent', agent)
        config.pop('skip', None)
        start_flow = agent.start_flow
        # total_pages = sapi.total_pages()  # TODO
        # head_intents = sapi.flows_in_page()  # TODO
        # total_phrases = ...  # TODO
        stat = {
            **config,
            'agent': config['agent_name'],
            'notes': config.get('notes'),
            'intents': len(sapi.list_intents(agent_id)),
            'flows': len(sapi.list_flows(agent_id)),
            'latest': True,
            'display_name': agent.display_name,
            'start_flow': start_flow,
            # 'region': agent.region
            # 'pages': len(sapi.list_pages(agent_id) ),
            # 'webhooks': len(sapi.list_webhooks(agent_id) ),
        }
        # stat.update(config)
        stats.append(stat)
        logit.obj('stat', stat)
        df = pd.DataFrame(stat, index=[0])
        flowstats.save_stat(df, stat, stats_config)
        time.sleep(0.5)

    # print(df.head())
