'''
dig into conversations for insights

    * chat_logs - line by line / turn by turn raw logs for each chat

    * convo_stats - summary row per conversation

    * page_stats
        aggregation of convo stats per page
        - page
        - flow
        - last_driver
        - total = total event count
        - escalated
        - tc_guess_total = TC true guessed
        - tc_guess_pct = tc_guess_total / volume
        - tc_label_pct - percentage
        - no_match_pct - pct of no-matches
        - escalate_pct - pct of people asking for operator


    convo_graph - pages and intents as nodes and edges
        groupby on chat_logs to get counts for graphing
        - page
        - intent
        - count

    convo_steps - forward and reverse steps per conversation
        convo | fs00...fs10 | rs00..rs10 | path

'''
import logging

import pandas as pd
import numpy as np

from cxutils import logit
from cxutils.sheeter import Sheeter
from cxutils import biglib
from cxutils import gbot
from cxutils import cleaner

from config import configlib

from models.test_set import TestSet

# TODO modify for your env
SESSION_STUB = "projects/CUSTOMER-it-pr-pp4v-ppv4-0/locations/global/agents/xxxxx/environments/yyyy/sessions/"


class Digger:
    '''dig for insights
    calculate conversation lengths and other stats
    save to 'convos' tab on same gdoc
    '''

    def __init__(self, set_name):
        '''dig for insights
        args:
            update_doc: update data back to original gdoc
        '''
        self.set_name = set_name
        self.doc = None
        self.tabname = None
        # self.update_doc = True
        self.df = None
        self.doc_info = None
        self.init_gdoc()
        # self.fetch_gdoc()
        # print('loaded test_set:', self.df.shape)

    def init_gdoc(self):
        '''fetch data from a gdoc'''
        self.doc_info = configlib.get_gdoc_info(cname=self.set_name)
        self.tabname = self.doc_info['tabname']
        self.doc = Sheeter(sheet_id=self.doc_info['sheet_id'])

    def fetch_gdoc(self):
        self.df = self.doc.read_tab(self.tabname)
        logging.info('loaded gdoc len: %s', len(self.df))

    def fetch_bq(self):
        '''fetch df data from BQ'''
        where = f'where set_name="{self.set_name}" '
        table_id = biglib.make_table_id('xp_convos')
        query = f'''select * from {table_id} {where} '''
        self.df = biglib.query_df(query)

    def rename_columns(self):
        """logs and DB field names don't match up"""
        self.df.rename(columns={
            'user_request': 'utterance',
            'intent_display_name': 'intent'
        }, inplace=True)
        logging.info('renamed columns: %s', self.df.columns)

    def process(self):
        '''do pipeline of cleanups'''
        self.rename_columns()
        self.remove_blank_input()
        self.clean_session()
        self.guess_basics()
        # self.mark_start('head_intent.bill_explain_incorrect')
        self.count_turns()
        self.calc_paths(write_doc=True)
        # self.doc.write_tab(self.tabname, self.df)

    def clean_session(self):
        '''remove extra fat from columns'''
        junk = SESSION_STUB
        self.df['convo'] = self.df['session'].map(lambda x: x.lstrip(junk))

    def remove_blank_input(self):
        '''remove no user input'''
        self.df['utterance'].replace(
            '', np.nan, inplace=True)  # have to convert to use dropna
        self.df.dropna(subset=['utterance'], inplace=True)
        print('removed blanks:', self.df.shape)

    def mark_start(self, intent_name):
        '''mark start turns based on a specific intent we're looking for
        useful when you want to count the distance from a particular point
        '''
        def is_start(val):
            if val == intent_name:
                return True
            return False
        self.df['start'] = self.df['actual'].map(is_start)
        # head_intent.bill_explain_incorrect

    def count_turns(self):
        '''count depth into conversation'''
        logging.info('count turns')
        turn = 1
        convo_count = 0
        last_convo = None

        self.df['convo_id'] = 0  # empty column

        for _index, row in self.df.iterrows():
            # gspread UI brings in '1' as a string :(
            # start = row['start']
            if row['convo'] != last_convo:
                row['start'] = True
                turn = 1
                convo_count += 1
                last_convo = row['convo']
            else:
                turn += 1
            row['turn'] = turn
            row['convo_id'] = convo_count

        logging.info('convo count: %s', convo_count)
        logging.info('head %s', self.df.head(3))
        logging.info(
            'turns \n%s', self.df[['utterance', 'start', 'turn', 'convo_id']])

    def guess_one(self, text):
        '''guess basic intents to save queries to DFCX'''
        intent = None
        if text == 'yes':
            intent = 'confirmation.yes'
        if text == 'no':
            intent = 'confirmation.no'

        # logging.info('guess %s = %s', text, intent)
        return intent

    def guess_basics(self):
        '''update `actual` and guess yes/no columns for empties'''
        # df = self.df[:20]
        # df = self.df

        # updates rows in place in df
        for _index, row in self.df.iterrows():
            if row['intent'] != '':
                row['actual'] = row['intent']
            else:
                row['actual'] = self.guess_one(row['utterance'])

        print('basics:', self.df)
        # logging.info('basics \n%s', self.df[['utterance', 'actual']])

    @staticmethod
    def make_path(items):
        '''concat a list of items but remove blanks'''
        if not items or len(items) == 0:
            return ''

        safe = [str(item) for item in items]
        return ' >> '.join(safe)

    def calc_paths(self, write_doc=True):
        '''calculate paths'''
        df = self.df
        convo_groups = df.groupby('convo')
        convos = []
        for key, convo in convo_groups:
            #
            path = convo['intent'].values.tolist()
            utts = convo['utterance'].values.tolist()
            turns = len(path)
            experiment = convo['xp'].iloc[0]
            convo = {
                'is_xp': convo['is_xp'].iloc[0],
                'escalated': convo['escalated'].iloc[0],
                'convo': key,
                'xp': experiment,
                'turns': turns,
                'path': Digger.make_path(path),
                'utts': Digger.make_path(utts),
            }
            # log the first 5 steps in detail
            # have to pad all values with None or gspread will crash
            for num in range(5):
                if num >= turns:
                    val = None
                    utt = None
                else:
                    val = path[num]
                    utt = utts[num]
                convo[f't{num}'] = val
                convo[f'utt{num}'] = utt
            # print('convo', convo)
            convos.append(convo)

        logging.info('convos len: %s', len(convos))
        convos_df = pd.DataFrame(convos)
        logging.info('convos_df \n%s', convos_df.head(20))
        if write_doc:
            self.write_convos(convos_df)

    def write_convos(self, convos):
        '''write convos summary to same sheet in 'convos' tab'''
        tabname = 'convos'
        self.doc.write_tab(tabname, convos)
        # TODO write to xp_paths
