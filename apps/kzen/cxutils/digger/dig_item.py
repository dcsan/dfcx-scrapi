"""base class for Dig Items - ChatLogs, ChatPaths etc.
basically BQ backed objects
that can also read/write to google sheet
"""
from __future__ import annotations
from google.cloud.bigquery import table
from icecream import IceCreamDebugger

import logging
import pandas as pd
from cxutils import biglib
from cxutils.sheeter import Sheeter
# import csv

from cxutils.dclib import dclib

ic = IceCreamDebugger(prefix='dig_item', includeContext=False)


class DigItem:
    """base class for diggables"""

    def __init__(self, set_name):
        self.set_name = set_name
        self.tabname = None
        self.df = None  # as dataframe
        self.data = None  # as dict/list
        self.doc_info = None
        self.sheet = None
        # defined in subclass but declare it here for linter
        self.table_id = None

    def sample(self, count=20):
        """take a subsample"""
        self.df = self.df[0:count]

    def init_sheet(self, cname: str = None, tabname=None):
        """create spreader instance"""
        cname = cname or self.set_name
        self.sheet = Sheeter(cname=cname)
        self.tabname = tabname
        return self.sheet

    def read_gdoc(self, tabname=None, cname: str = None) -> pd.DataFrame:
        '''fetch data from a gdoc'''
        # we use a different sheet from the chat_logs
        if not self.sheet or cname:
            cname = cname or self.set_name
            self.init_sheet(cname=cname)
        if tabname is not None:
            self.tabname = tabname
        self.df = self.sheet.read_tab(self.tabname)
        # logging.info('loaded gdoc len: %s', len(self.df))
        ic('loaded gdoc len: ', len(self.df))
        return self.df

    def read_gdoc_as_dict(self, tabname=None, cname: str = None):
        if not self.sheet or cname:
            self.init_sheet(cname=cname)
        if tabname:
            self.tabname = tabname
        self.data = self.sheet.read_as_dict(self.tabname)
        ic('read gdoc as dict len:', len(self.data))
        return self.data

    def write_gdoc(self, cname=None, tabname=None, df=None):
        '''write a copy of the data to a google sheet'''
        if not self.sheet and not cname:
            cname = self.set_name
        if cname:
            if tabname:
                self.init_sheet(cname, tabname)
            else:
                logging.error('no gdoc sheet: %s, cname: %s, tabname: %s',
                              self.sheet, cname, tabname)
                raise KeyError('need to configure gdoc for writing')
        df = df if df is not None else self.df
        ic({'write to gdoc tabname', tabname})
        self.sheet.write_tab(tabname=tabname, df=df)

    def from_dict(self, obj):
        """create df from a dict, mainly for testing"""
        self.df = pd.DataFrame(obj)

    def read_csv(self, fpath):
        """from a csv for testing"""
        self.df = pd.read_csv(fpath)

    def fetch_bq(self):
        '''fetch df data from BQ'''
        where = f'where set_name="{self.set_name}" '
        query = f'''select * from {self.table_id} {where} '''
        self.df = biglib.query_df(query)
        logging.info('fetch_bq set_name=%s, len %s',
                     self.set_name, len(self.df))
        return self.df

    def set_column(self, col, value):
        """adding a column eg for xp name"""
        self.df[col] = value

    def delete_bq_set(self, table_id=None):
        """delete by set_name"""
        table_id = table_id or self.table_id
        query = f"delete from {table_id} where set_name='{self.set_name}' "
        biglib.query(query)

    def write_bq(self, df: pd.DataFrame = None, delete_first=True, table_id=None):
        """write the DF out to BigQuery"""
        table_id = table_id or self.table_id
        df = df if df is not None else self.df
        if delete_first:
            self.delete_bq_set()
        logging.info('write to bq len: %s', len(df))
        logging.info('df.head\n%s', df.head(2))
        biglib.insert_df(df, table_id=table_id)

    def debug_df(self: DigItem, df):
        """common debug commands for DF"""
        df = df if df is not None else self.df
        logging.info('--- df.head \n%s', df.head(3))
        logging.info('--- df.rows \n%s', df.head(3).transpose())
        # logging.info(
        #     'turns \n%s', self.df[['page', 'page_from', 'start', 'turn', 'convo_id']])

    # def reorder_columns(self, columns):
    #     self.df = dclib.reorder_columns(self.df, columns)
        # print('columns before', self.df.columns)
        # remain = [col for col in list(self.df.columns) if col not in columns]
        # columns += remain
        # try:
        #     self.df = self.df.reindex(columns, axis=1)
        # except ValueError as err:
        #     logging.error('failed to reorder columns %s',
        #                   sorted(self.df.columns))
        #     raise err
        #     # print('columns after', self.df.columns)
