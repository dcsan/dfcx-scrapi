'''updating agents'''

import logging
import json

from typing import List

# this doesnt exist anymore
# from dfcx_scrapi.tools.dataframe_functions import DataframeFunctions
from cxutils.sapiwrap.mega_agent import MegaAgent


# from dfcx_scrapi.core.sapi_base import SapiBase

# from cxutils.testrunner.testrunner import TestRunner
# from cxutils.benchmarker.benchmarker import BenchMarker


from models.test_set import TestSet

# from cxutils.sheeter import Sheeter
from config import configlib
from config import base_config


RUN_CONFIGS = [

    {
        'cname': 'bill_custom',
        'agent_before': 'agent_before',
        'target_agent': 'agent_after',
        'set_name': 'BILL-testset',  # custom india pod test_set
        'use_case': 'BILL',
        # 'updated_intents': 'BILL-intents-v3',
        'sample': False,
        'reload': True,  # reload data from gdocs
    },

    {
        'cname': 'bill_silver',
        'agent_before': 'agent_before',
        'target_agent': 'agent_after',
        'set_name': 'SET-NAME',
        'use_case': 'BILL',
        # 'updated_intents': 'BILL-intents-v3',
        'sample': False,
        'reload': True,  # reload data from gdocs
    },

    {
        # dry run on april-MR-copy
        'cname': 'april_mr_dryrun',
        'cmd': 'update_intents',
        'updated_intents': 'SALES-updated-intents',
        # 'target_agent': 'agent_after',
        'target_agent': 'AGENT-ID',
        'sample': False
    },

    {
        # update CUSTOMER April MR
        'cname': 'sales_remap_ext',
        'cmd': 'update_intents',
        'updated_intents': 'SALES-updated-intents',
        'target_agent': 'AGENT-ID',
        'sample': False,
        'reload': True
    },

]


class Kzen:
    '''benchmark before, update a set of intents, and run after'''

    def __init__(self, cname: str):
        '''setup the kzen run'''
        configlib.fetch_all_configs()
        cfg = self.runconfig = self.get_run_config(cname)
        agent_info = configlib.get_agent(cfg['target_agent'])
        creds_path = agent_info.get(
            'creds_path') or base_config.read('DEFAULT_CREDS_PATH')

        self.agent_info = agent_info
        # this is broken due to upstream SAPI breaking changes
        self.sapi = MegaAgent(creds_path=creds_path,
                              agent_path=agent_info.get('agent_path'))
        self.run_one(cfg)

    def run_one(self, cfg):
        '''run a kzen pipeline'''
        # self.run_before()
        cmd = cfg.get('cmd')
        self.prepare(cfg)

        if not cmd:
            logging.error('no cmd found %s', cfg)
            return

        if cmd is 'update_intents':
            self.update_intents(cfg)

    def get_run_config(self, cname):
        '''get from gdoc / BQ'''
        # FIX ME - for some reason we can't have values with a `-` in them?
        logging.info('looking for %s', cname)
        try:
            # runconfig = next(elem for elem in RUN_CONFIGS if elem['cname'] is cname) # first
            runconfigs = [
                elem for elem in RUN_CONFIGS if elem['cname'] is cname]
        except StopIteration:
            logging.error('Stop cname [%s] not found in runconfigs %s', cname, json.dumps(
                RUN_CONFIGS, indent=2))
        if not runconfigs:
            logging.error('no configs? cname %s not found in runconfigs %s',
                          cname, json.dumps(RUN_CONFIGS, indent=2))

        return runconfigs[0]

    # def filter_bill(self):
    #     '''filter for just BILL mentioning intents'''
    #     test_set = TestSet()
    #     # df = test_set.fetch_from_gdoc(cname='test_set_name') # load into BQ.test_sets
    #     df = test_set.read_bq('test_set_name_3.2') # could maybe do a where % clause
    #     # logging.info('full set %s', len(df))
    #     df = df[df['intent'].str.contains('bill', case=False, na=False) ]
    #     logging.info('bill set %s', len(df))
    #     # df.head(100)
    #     return df

    def prepare(self, cfg):
        '''load gdoc into bq based on cname of doc in config sheet'''
        if not self.runconfig.get('reload'):
            return
        test_set = TestSet()
        if cfg.get('set_name'):
            # load into BQ.test_sets
            test_set.fetch_from_gdoc(cname=self.runconfig['set_name'])
        if cfg.get('updated_intents'):
            logging.info('reload updated_intents')
            # load into BQ.test_sets
            test_set.fetch_from_gdoc(cname=cfg['updated_intents'])

        # self.list_intents_before(agent_name=self.runconfig['target_agent'])

        # print(_df.head(200))
        # TODO - restore bot from .blob file and retrain it
        # wait for training to complete

    # def run_before(self):
    #     '''run a benchmark *before* any changes'''
    #     logging.info('run_before : using runconfig %s', self.runconfig)
    #     bench = BenchRun(
    #         agent_name=self.runconfig['agent_before'], **self.runconfig)
    #     bench.run(sample=self.runconfig['sample'])

    # def run_after(self):
    #     '''run BM again after intents are updated'''
    #     logging.info('run_after')
    #     bench = BenchRun(
    #         agent_name=self.runconfig['target_agent'], **self.runconfig)
    #     bench.run(sample=self.runconfig['sample'])

    def update_intents(self, cfg):
        '''update intents inplace in the target agent'''
        # self.test_set.fetch_from_gdoc(cname=self.runconfig['set_name']) # load into BQ.test_sets

        intent_set = TestSet.read_bq(cfg['updated_intents'])
        intent_set = self.reshape_intents(intent_set)

        agent_info = configlib.get_agent(cfg['target_agent'])
        logging.info('target_agent %s', agent_info)
        agent_path = agent_info['agent_path']
        creds_path = agent_info.get(
            'creds_path') or base_config.read("default_creds_path")
        dafx = DataframeFunctions(creds_path)
        result = dafx.bulk_update_intents_from_dataframe(
            agent_id=agent_path,
            train_phrases_df=intent_set,
            update_flag=True
        )
        logging.info('bulk_update %s', len(result))
        return result

    def reshape_intents(self, df):
        '''reshape how the bulk update func wants'''
        if 'display_name' not in df.columns:
            df['display_name'] = df['intent']  # or df['expect']
        if 'text' not in df.columns:
            df['text'] = df['utterance']  # or df['phrase']
        print('final df', df)
        return df

    def list_intents_before(self, agent_name):
        '''list intents in the target agent to help prepare / filter which intents we want'''
        logging.info('agent_id %s', agent_name)
        agent_info = configlib.get_agent(agent_name)
        agent_path = agent_info['agent_path']
        intents = self.sapi.list_intents()
        intent_names = [intent.display_name for intent in intents]
        # logging.info('intent_names %s', intent_names)
        for name in intent_names:
            print(name)

    # def fetch_intents(self, cname, _intents_filter=None):
    #     docinfo = configlib.get_gdoc_info(cname)
    #     test_set = TestSet()
    #     df = test_set.fetch_from_gdoc(cname=cname)
    #     test_set.write_bq(df, set_name=cname)

    # def fetch_phrases(self, _intent_names: List[str], _set_name: str):
    #     '''fetch a list of phrases from BQ'''
    #     return([
    #         'one', 'two', 'three'
    #     ])

# class Updater:
#     '''class for updating agents'''

#     @staticmethod
#     def udpate(agent, intent_id):
#         '''update an intent in agent'''
#         # intent_id = intent_id
#         self.dfcx.update_intent(intent_id=intent_id, obj=intent)
