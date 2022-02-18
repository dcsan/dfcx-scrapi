from numpy import delete
from config.base_config import BaseConfig
import logging
import pandas as pd

from lib.data.biglib import BigLib
from lib.util import dflib
from tools.digby.diggable import Diggable
from config.base_config import BaseConfig
from lib.data.sheeter import Sheeter


class Ingester(Diggable):

    target_table_id: str
    source_table_id: str

    def __init__(self,
                 config: BaseConfig,
                 where: str = '',
                 limit: str = ''
                 ):
        super().__init__(config=config, where=where, table_name='fbl_raw', limit=limit)
        self.source_table_id: str = self.config['upstream_table_id']
        self.target_table_id: str = self.config['raw_table_id']

    def simple_clean(self, raw_data):
        '''fix only serious problems in data'''

        # only select columns with an actor - PROBLEM this skips first line of conversation
        # raw_data = raw_data[~(raw_data['role'].isna())]

        fbl_data = raw_data.copy().sort_values(
            by=['session_id', 'position'])

        # what does this do????  KeyError: 'CUSTOMER'
        # make sure sequence is Agent, Customer, Agent
        # fbl_data = fbl_data[(fbl_data['actor'] == role_type_map['CUSTOMER'])
        #                     & (fbl_data['prev_actor'] == role_type_map['AGENT'])
        #                     & (fbl_data['next_actor'] == role_type_map['AGENT'])]

        return fbl_data

    def pipeline(self, delete_first=False):
        self.df = self.simple_clean(self.df)
        self.df = self.coerce_fields(self.df)

        if delete_first:
            BigLib.truncate(table_name='fbl_raw')
        BigLib.insert_df(self.df, table_id=self.target_table_id)
        return self.df

    def coerce_fields(self, df):
        '''data from sheets has "null" as a string'''
        df = df.replace('null', None)
        return df

    def fetch_csv(self, fpath, delete_first=False):
        self.df = pd.read_csv(fpath)
        self.pipeline(delete_first=delete_first)
        return self.df

    def fetch_upstream_sheet(self, doc_name, delete_first=False):
        """fetch from a sheet"""
        sheet = Sheeter(self.config)
        sheet.open_by_name(doc_name)
        self.df = sheet.read_tab(tab_index=0)
        self.pipeline(delete_first=delete_first)
        return self.df

    def fetch_upstream_table(self, delete_first=False):
        """fetch from a BQ table"""
        # move data between datasets
        # TODO - use batch bq transfer commands?
        # https://cloud.google.com/bigquery/docs/copying-datasets
        # cls.configure()

        where = self.where or 'where TRUE'
        logging.info('grab from %s => %s',
                     self.source_table_id,
                     self.target_table_id)
        qs = f'''
            select * from `{self.source_table_id}`
            {where}
            AND role is not null
            ORDER BY
                session_id, position
            '''
        df = BigLib.query_df(qs)
        logging.info('count: %s', df.shape[0])

        if delete_first:
            qs = f'delete from {self.target_table_id} where TRUE'
            BigLib.query(qs)

        BigLib.insert_df(df, table_id=self.target_table_id)
        self.df = df
        return df
