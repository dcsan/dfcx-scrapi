"""base class for Dig Items - ChatLogs, ChatPaths etc.
basically BQ backed objects
that can also read/write to google sheet
"""
# from __future__ import annotations
from google.cloud.bigquery import table
from icecream import IceCreamDebugger

import logging
import pandas as pd

from lib.data.biglib import BigLib
from lib.util import dflib
from lib.data.sheeter import Sheeter
from config.base_config import BaseConfig

# import csv

from lib.util import dclib

ic = IceCreamDebugger(prefix='dig_item', includeContext=False)


class Diggable:
    """base class for diggables which are BQ table backed"""

    where: str = ''
    limit: str = ''
    config: BaseConfig
    df: pd.DataFrame
    sheet: Sheeter
    tabname: str
    table_id: str

    def __init__(self,
                 df: pd.DataFrame = None, config={}, where='',
                 table_name='',
                 limit=''):
        # self.tabname = None
        # self.df = None  # as dataframe
        # self.data = None  # as dict/list
        # self.doc_info = None
        # self.sheet = None
        self.table_id = BigLib.make_table_id(table_name)
        self.config = config
        self.where = where
        if df is not None:
            self.df = df

    def sample(self, count=20):
        """take a subsample"""
        # self.df = self.df[0:count]
        self.df = self.df.head(count)

    # def init_sheet(self, cname: str = None, tabname=None):
    #     """create spreader instance"""
    #     cname = cname or self.set_name
    #     self.sheet = Sheeter(self.config)
    #     self.tabname = tabname
    #     return self.sheet

    # def read_gdoc(self, tabname=None, cname: str = None) -> pd.DataFrame:
    #     '''fetch data from a gdoc'''
    #     # we use a different sheet from the chat_logs
    #     if not self.sheet or cname:
    #         cname = cname or self.set_name
    #         self.init_sheet(cname=cname)
    #     if tabname is not None:
    #         self.tabname = tabname
    #     self.df = self.sheet.read_tab(self.tabname)
    #     # logging.info('loaded gdoc len: %s', len(self.df))
    #     ic('loaded gdoc len: ', len(self.df))
    #     return self.df

    # def read_gdoc_as_dict(self, tabname=None, cname: str = None):
    #     if not self.sheet or cname:
    #         self.init_sheet(cname=cname)
    #     if tabname:
    #         self.tabname = tabname
    #     self.data = self.sheet.read_as_dict(self.tabname)
    #     ic('read gdoc as dict len:', len(self.data))
    #     return self.data

    # def write_gdoc(self, cname=None, tabname=None, df=None):
    #     '''write a copy of the data to a google sheet'''
    #     if not self.sheet and not cname:
    #         cname = self.set_name
    #     if cname:
    #         if tabname:
    #             self.init_sheet(cname, tabname)
    #         else:
    #             logging.error('no gdoc sheet: %s, cname: %s, tabname: %s',
    #                           self.sheet, cname, tabname)
    #             raise KeyError('need to configure gdoc for writing')
    #     df = df if df is not None else self.df
    #     ic({'write to gdoc tabname', tabname})
    #     self.sheet.write_tab(tabname=tabname, df=df)

    # def from_dict(self, obj):
    #     """create df from a dict, mainly for testing"""
    #     self.df = pd.DataFrame(obj)

    # def read_csv(self, fpath):
    #     """from a csv for testing"""
    #     self.df = pd.read_csv(fpath)

    def read_bq(self, where: str = None, limit=None):
        '''fetch df data from BQ'''
        where = where or self.where
        limit = limit or self.limit
        order = 'order by session_id, position asc'
        query = f'''select * from {self.table_id} {where} {order}'''
        if limit:
            query = f'{query} LIMIT {limit}'
        self.df = BigLib.query_df(query)
        logging.info('%s fetch_bq where=%s, len %s',
                     self.__class__.__name__, where, len(self.df))
        return self.df

    def set_column(self, col, value):
        """adding a column eg for xp name"""
        self.df[col] = value

    def rename_columns(self):
        class_name = self.__class__.__name__
        renames = self.config['rename_columns']
        logging.info('renaming columns in %s', class_name)
        self.df = dflib.rename_columns(self.df, renames)
        return self.df

    def reorder_columns(self):
        self.df = dflib.reorder_columns(
            self.df, self.config['reorder_columns'])
        self.show_columns()

    def show_columns(self):
        colnames = list(self.df.columns)
        # logging.info('renamed columns %s', '\n'.join(colnames))

    def delete_bq(self, table_id=None, where: str = None):
        """delete by set_name"""
        where = where or self.where
        if not where:
            return logging.error('cannot delete without where clause')
        table_id = table_id or self.table_id
        query = f"delete from {table_id} {where} "
        BigLib.query(query)

    def write_bq(self, df: pd.DataFrame = None, delete_first=True, table_id=None):
        """write the DF out to BigQuery"""
        table_id = table_id or self.table_id
        df = df if df is not None else self.df
        if delete_first:
            self.delete_bq()
        logging.info('write to bq len: %s', len(df))
        logging.info('df.head\n%s', df.head(2))
        BigLib.insert_df(df, table_id=table_id)

    # def debug_df(self: DigItem, df):
    #     """common debug commands for DF"""
    #     df = df if df is not None else self.df
    #     logging.info('--- df.head \n%s', df.head(3))
    #     logging.info('--- df.rows \n%s', df.head(3).transpose())
    #     # logging.info(
    #     #     'turns \n%s', self.df[['page', 'page_from', 'start', 'turn', 'convo_id']])

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
