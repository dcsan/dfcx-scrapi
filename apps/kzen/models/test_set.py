"""
loading test_sets of utterance:intents
this class wraps the test sets that are in the google docs

note this does NOT have any contained data,
its mostly a wrapper class method loads data into BQ

expects a minimum format like
    utterance   intent

will add:
    set_name

we also store fields from the original gdoc:
    num, subtopic, use_case, comment

on reading in we also reject any lines that have '[redacted]' in them

TODO -
    refactor to keep data/dataframe internal and provide accessor methods,
    so that we can provide a typechecked API on the data

"""
import logging
import re

# from typing import List  # Python 3.8 and earlier

from cxutils.sheeter import Sheeter
from cxutils import biglib
from config import configlib
from models.bq_base import BqBase
import pandas as pd


class TestSet(BqBase):
    """wrapper on BQ backed testset"""

    data: pd.DataFrame

    def __init__(self, set_name: str):
        if not set_name:
            raise ValueError("TestSet needs a set_name")
        self.table_id = biglib.make_table_id('test_sets')
        # self.data = []
        self.set_name = set_name
        super().__init__()

    @staticmethod
    def reject_filter(val, rex):
        """reject rows based on rex match, eg for [redacted] items"""
        # logging.info('filter rex: %s | val %s', rex, val)
        if val:
            mobj = re.search(rex, val)
            if mobj:
                logging.info('reject: %s', val)
                return False
            else:
                return True
        else:
            return True

    def fetch_from_gdoc(self, cname: str) -> pd.DataFrame:
        """initial load of gdoc into BQ
            cname is a 'nickname' of a google doc found in the configs table
            this is an instance method so it can write to the BQ table
        """
        doc_info = configlib.get_gdoc_info(cname=cname)
        logging.info('doc_info: %s', doc_info)
        tabname = doc_info['tabname']
        # logging.info('load_gdoc %s / %s', cname, tabname)
        doc = Sheeter(sheet_id=doc_info['sheet_id'])
        df = doc.read_tab(tabname)

        # if 'delete' in df.columns:
        #     df = df[df['delete'] != True]  # NOT an error ignore linter

        # TODO - filter out DELETE and REVIEW items
        # optional - reject [redacted] utterances since they will probaly fail anyway
        # rex = 'redacted'  # doesn't need the [] to avoid regex complexity
        # df = df[df['utterance'].apply(TestSet.reject_filter, rex=rex)]

        df = TestSet.normalize_column_names(df)

        # print('TestSet.fetch df\n', df.head())
        self.write_bq(df, set_name=cname)
        # print('df', df.info() )
        self.data = df
        return df

    def write_bq(self, df, set_name='tag'):
        """write df to bq usually when loading from gdoc
        """
        # qs = f'''delete from {self.table_id} where set_name="{set_name}" '''
        # biglib.query(qs)
        where = f"set_name='{set_name}'"
        # FIXME - could be a class method since we always can calculate the table_id
        biglib.delete(where=where, table_id=self.table_id)
        df['set_name'] = set_name
        logging.info('TestSet.write_bq: df \n %s', df.head())
        biglib.insert_df(table_name='test_sets', df=df, if_exists='append')
        biglib.add_uuids(table_name='test_sets')

    @classmethod
    def read_bq(cls, set_name) -> pd.DataFrame:
        # FIXME - why is this a class method and above is an instance method...?
        """load set from bq table"""
        # TODO - refactor so doesnt have to be a classmethod?
        where = f"set_name='{set_name}'"
        df = biglib.get_df(where=where, table_name='test_sets')
        # logging.info('loaded\n %s', df.head())

        # normalize column names
        df = cls.normalize_column_names(df)

        df['set_name'] = set_name
        # logging.info('TestSet.read_bq \n%s', df.head())
        return df

    @classmethod
    def normalize_column_names(cls, df) -> pd.DataFrame:
        '''use generic names for columns so the test_set can be reused
        eg utterance -> text, intent -> expect
        '''
        # logging.info('before\n %s', df.head())
        df = df.rename(columns={
            'intent': 'expect',
            "utterance": "text",
            'phrase': 'text'
        })
        logging.info('after\n %s', df.head())
        TestSet.verify_data(df)
        return df

    @classmethod
    def verify_data(cls, df):
        '''check minimum required data exists'''
        check = True
        if 'text' not in df.columns:
            logging.error('no text column in dataframe \n%s', df)
            check = False

        if 'expect' not in df.columns:
            logging.error('no expect column in dataframe \n%s', df)
            check = False

        # if 'intent' in df.columns:
        #     df.drop(['intent'], axis=1)

        if not check:
            logging.error('test_set columns \ntext: %s \n:intent %s',
                          df.text, df.intent)
            logging.info('test_set columns: \n%s', df.columns)
        else:
            logging.info('test_set verify OK')

    def load_intents(self, set_name=None):
        """load intents from bq table"""
        set_name = set_name or self.set_name
        table_id = biglib.make_table_id('test_sets')
        query = f'select distinct intent from {table_id} where set_name="{set_name}" '
        items = biglib.query_list(query)
        logging.info('TestSet.intents [%s]', len(items))
        return items

    def load_phrases(self, intent_name, set_name=None, limit=0):
        """load set from bq table"""
        set_name = set_name or self.set_name
        table_id = biglib.make_table_id('test_sets')
        if intent_name and len(intent_name) > 1:
            intent_filter = f'and intent="{intent_name}" '
        else:
            intent_filter = ''
        # safest to select * since we also overwrite the data back out
        limit = limit if limit > 0 else 10000
        query = f'''
            select *
            from {table_id}
            where set_name="{set_name}"
            {intent_filter}
            order by sim_count DESC, utterance ASC
            limit {limit}
        '''
        plist = biglib.query_list(query)
        logging.info('phrases \n%s', len(plist))
        return plist

    def debug_set(self, df, columns):
        """show some columns"""
        print(df[['uuid', 'sim_count']])
