from tools.logger import logger  # do this first to set logging format

import pandas as pd

from config.base_config import BaseConfig
# import sys

from lib.data.sheeter import Sheeter
import logging

from config.client_config import clientConfig

from tools.hotspots import Hotspot
# from tools.grabber import Grabber
from tools.digby.ingester import Ingester
from tools.digby.chat_log import ChatLog
from tools.digby.convo_log import ConvoLog
from lib.data.biglib import BigLib

from tools.installer import Installer


class BaseRouter():

    config: BaseConfig

    @classmethod
    def setup(cls, config: BaseConfig):
        '''call once per session'''
        cls.config = config
        BigLib.configure(config)

    @classmethod
    def migrate(cls, config):
        '''recreate all the tables from schemas'''
        Installer.create_tables(config)

    @classmethod
    def no_matches(cls):
        df = Hotspot.get_no_matches(limit=1000)
        df.to_csv('data/ignored/no_matches_raw.csv')
        print(df.head())

        df = Hotspot.group_no_matches()
        df.to_csv('data/ignored/no_matches_counts.csv')
        print(df.head(50))

    # @staticmethod
    # def paths():
    #     df = Hotspot.group_calls()
    #     print(df.head(40))

    # @classmethod
    # def fetch_upstream(cls):
    #     # run this once per session to grab latest data from upstream
    #     Ingester.fetch_upstream(config=cls.config)

    @classmethod
    def ingest_upstream_table(cls, delete_first=True, where='', limit='LIMIT 50000', fname=None):
        # where = where or 'WHERE current_sprint_number="9" '  # use original LOOONG names
        ingester = Ingester(
            where=where,  # yes, number is a string
            limit=limit,
            config=cls.config
        )
        df = ingester.fetch_upstream_table()
        df = ingester.pipeline(delete_first=delete_first)
        # self.df = df
        # df = ingester.read_bq(where=where)

        fname = fname or 'ingest-raw.csv'
        fpath = f'data/ignored/{fname}'

        # logging.info('columns\n%s', df.columns)
        df.to_csv(fpath)
        logging.info('ingested: %s items to %s', len(df), fpath)
        return df

    @classmethod
    def ingest_upstream_sheet(cls, doc_name, delete_first=True):
        ingester = Ingester(
            config=cls.config
        )
        df = ingester.fetch_upstream_sheet(
            delete_first=delete_first, doc_name=doc_name)

        # df.to_csv('data/ignored/chat_ingest.csv')
        logging.info('ingested: %s', len(df))
        return df

    @classmethod
    def clear_tabs(cls, config: BaseConfig):
        config = config or cls.config
        sheet = Sheeter(config, sheet_id=config['sheets']['ChatParser'])
        sheet.clear_tab('raw')
        sheet.clear_tab('chat_min')
        sheet.clear_tab('chat_log')
        sheet.clear_tab('convo_log')

    @classmethod
    def process(cls, df: pd.DataFrame, config: BaseConfig = None, sample=None, to_sheets=True, truncate=True, where=None):
        '''run the full pipeline'''
        config = config or cls.config
        df = df.fillna('')
        df.sort_values(['session_id', 'position'], inplace=True)

        sheet = None
        if to_sheets:
            sheet = Sheeter(config=config)
            sheet.open_by_id(sheet_id=config['sheets']['ChatParser'])

        if sample:
            df = df[:sample]  # for quicker runs

        if sheet:
            sheet.write_tab(df, tabname='raw')

        # ---- chatlog - pass in a DF is ok
        if truncate:
            BigLib.truncate(table_name='chat_logs')
        chat_log = ChatLog(config=config, where=where)
        chat_log.pipeline(df=df)  # read df from bq
        # chat_log.df.to_csv('data/ignored/chat_logs.csv')

        if sheet:
            sheet.write_tab(chat_log.df, tabname='chat_log')
            # sheet.write_tab(chat_log.minimize(), tabname='chat_min')
        # logging.info('wrote chatlogs \n%s', chat_log.df.columns)

        # ---- convo_log - has to read from chat_log BQ for aggregations
        if truncate:
            BigLib.truncate(table_name='convo_logs')
        convo_log = ConvoLog(config=config, where=where)
        df = convo_log.pipeline()
        # df.to_csv('data/ignored/convo_logs.csv')
        if sheet:
            sheet.write_tab(convo_log.df, tabname='convo_log')

        return {
            'convo_log': convo_log.df,
            'chat_log': chat_log.df
        }
        # print(df.head(10))
        # clogger.write_bq()

    @classmethod
    def testing(cls):
        pass
        # ingest into a DF
        # where = 'where sprint_number="9" '
        # df = Cli.ingest(delete_first=True, where=where)

    @classmethod
    def pull(cls, sprint=None, use_case=None, config=None, to_sheets=False, sample=None):

        BaseRouter.setup(config)  # do this first
        BaseRouter.clear_tabs(config)
        # Cli.migrate(config)

        # the schemas are different per pod

        where = '''WHERE channel="voice" '''
        if sprint:
            where = f'{where}\n AND sprint={sprint}'
        if use_case:
            where = f'{where}\n AND use_case="{use_case}" '

        BaseRouter.pipeline(config,
                            sample=sample,
                            to_sheets=to_sheets,
                            where=where)
