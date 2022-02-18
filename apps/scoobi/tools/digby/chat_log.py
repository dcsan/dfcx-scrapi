from os import read

from numpy import isin
from config.base_config import BaseConfig
import logging
from tools.digby.diggable import Diggable
import pandas as pd
import numpy as np

# from lib.data.biglib import BigLib
import typing
from tools.digby.diggable import Diggable

from tools.digby import chat_constants
from lib.util.text_util import TextUtil

# value of 'position' for first line of conversation - can be 1 or 2
# TODO - change to scan for "first line" after grouping since this is unreliable
FIRST_POSITION = 1


class ChatLog(Diggable):

    table_name = 'chat_logs'
    where: str

    def __init__(self, config: BaseConfig, df: pd.DataFrame = None, where=''):
        self.where = where
        super().__init__(df=df, config=config, where=where, table_name=self.table_name)

    def pipeline(self, df=None):
        if df is not None:
            self.df = df
        else:
            self.df = self.read_bq()
        self.rename_columns()
        self.dedupe_rows()  # before any shifting
        self.add_start_end()
        self.shifting()
        self.convert_bools()
        self.fill_missing()
        self.fill_down()
        self.calculate_exit()
        self.calc_all_paths()
        # calc paths after everything else
        self.reorder_columns()
        self.write_bq()  # have to write to BQ as convo_log only reads from BQ
        return self.df

    def fill_missing(self):
        '''fill in extra data'''
        # add reason column
        self.df['operator_check'] = self.df.apply(self.operator_check, axis=1)
        self.df['abandoned_check'] = self.df.apply(
            self.abandoned_check, axis=1)
        self.df['escalated_check'] = self.df.apply(
            self.escalated_check, axis=1)
        self.df['tc_check'] = self.df.apply(self.tc_check, axis=1)
        self.df['no_input_check'] = self.df.apply(self.no_input_check, axis=1)
        self.df['no_match_check'] = self.df.apply(self.no_match_check, axis=1)
        self.df['reason'] = self.df.apply(self.add_reason, axis=1)

    def calc_all_paths(self):
        self.df['page_path'] = self.df.apply(self.calc_page_path, axis=1)
        self.df['page_link'] = self.df.apply(self.calc_page_link, axis=1)

    def add_start_end(self):
        '''need these for later exit calc'''
        # TODO - group convos and then add first/last line
        # since it turns out `position` isn't reliable
        self.df["is_start"] = self.df["position"].map(
            lambda pos: 1 if pos == FIRST_POSITION else None)
        # self.df['is_start'] = self.df.apply(self.is_start, axis=1)
        self.df['is_end'] = self.df['is_start'].shift(-1)
        logging.info('se \n%s', self.df.head())

    def dedupe_rows(self):
        '''remove duplicate agent rows esp the last row'''
        self.df.drop_duplicates(
            subset=['session_id', 'role', 'page', 'content', 'position'], inplace=True)

    def shifting(self):
        """shift up or down the flows/pages/intents to align next result
        do this with groups so we don't move stuff across a session_id
        """
        df = self.df
        df['flow_target'] = df['flow']

        df['page_source'] = df.groupby('session_id')['page'].shift(1)
        df['page_target'] = df.groupby('session_id')['page'].shift(-1)
        # df['flow_source'] = df.groupby('session_id')['flow'].shift(-1)
        df['intent_target'] = df.groupby('session_id')['intent'].shift(-1)
        self.df = df

    # def is_start(self, row):
    #     if row.position == 1:
    #         return 1
    #     return None

    def convert_bools(self):
        '''convert some True/False columns to 1/0 for easier average/count etc math later'''
        # ignore 'handoff' as the data is bogus
        for col in ['escalated', 'abandoned', 'contained', 'fallback']:
            self.df[col] = self.df.apply(
                self.bool_to_int, axis=1, col=col)  # type: ignore

    # truthiness from google docs
    def bool_to_int(self, row, col):
        cell = row.get(col)
        if cell is True or \
                cell == 'TRUE' or\
                cell == 1:  # from google sheets
            return 1
        return 0

    def add_reason(self, row):
        '''add a reason column - intent or param filling
        so that every row has a reason for later aggregations'''
        if row.get('operator_check') == 1 or row.get('escalated_check') == 1:
            return 'escalated'
        else:
            return row.get('intent_target') or row.get('match_type') or None

    def calc_page_path(self, row):
        '''add a page_path column'''
        p1 = row.get('page_source')
        p2 = row.get('page_target')
        # check they're not nans
        if isinstance(p1, str) and isinstance(p2, str):
            return f"{p1} > {p2}"

    def calc_page_link(self, row):
        '''page > intent'''
        return f"{row.get('page_source')} > {row.get('intent_target')}"

    def escalated_check(self, row):
        '''check for bot utterance to if user escalated or not'''
        if row.get('position') == 1:
            return None  # 1st row is /projects/agent/1234
        text = row['content']
        if not isinstance(text, str):
            logging.warning('not text: %s \n%s', text, row)
            return None
        if not text:
            return None
        # if row['role'] is not 'AUTOMATED_AGENT':
        #     return None
        for line in chat_constants.ESCALATE_PHRASES:
            if line in text:
                return 1
        return None

    def abandoned_check(self, row):
        '''this is from the content field == 'Hangup'  '''
        text = row['content']
        if text == 'Hangup':
            return 1
        return None

    def no_input_check(self, row):
        if row['match_type'] == 'NO_INPUT':
            return 1
        if row['role'] == 'END_USER':
            text = row.get('content')
            if not text or text == 'NO_INPUT' or text == '':
                return 1
        return None

    def no_match_check(self, row):
        if row['match_type'] == 'NO_MATCH':
            return 1
        return None

    def tc_check(self, row):
        content = row.get('content')
        detail = row.get('detail')
        if not detail or pd.isna(detail):
            detail = 'NONE'
        if not content or pd.isna(content):
            content = 'NONE'
        for line in chat_constants.TASK_COMPLETE:
            if line in detail or line in content:
                return 1
        return None

    def operator_check(self, row):
        if row['is_start'] == 1:
            return None
        if row.get('intent_target') == 'Operator':
            return 1
        text = row['content']
        if isinstance(text, str):
            for word in chat_constants.OPERATOR_KEYWORDS:
                if word in text:
                    return 1
        return None

    def intent_detail(self, row):
        intent: str = row.get('intent_target')
        if isinstance(intent, str):
            if not TextUtil.contains(intent, chat_constants.VAGUE_INTENTS):
                return 1
        return None

    def fill_down(self):
        '''fill down columns for exit calcs'''
        # fill only works with nan so we have to replace empty/strings with nan first
        self.df['intent_last'] = self.df['intent_target']
        self.df.replace(r'^\s*$', np.nan, regex=True, inplace=True)

        subset_cols = ['intent_last', 'flow']
        [
            self.df[col].fillna(method='ffill', inplace=True)
            for col in subset_cols
        ]

    def completed_check(self, row):
        if row.get('exit') == 'COMPLETED':
            return 1
        return None

    def calc_exit(self, row):
        '''overwrite the target_page field based on results'''

        text = row.get('content')

        if TextUtil.contains(text, chat_constants.TASK_COMPLETE):
            return 'COMPLETED'
        if TextUtil.contains(row.get('detail'), chat_constants.TASK_COMPLETE):
            return 'COMPLETED'
        if row.get('tc_check') == 1:
            return 'COMPLETED'

        if TextUtil.contains(text, chat_constants.HANGUP_PHRASES):
            return 'ABANDONED'

        if row.get('escalated_check') == 1:
            return 'ESCALATED'

        if row.get('abandoned_check') == 1:
            return 'ABANDONED'

        if row.get('no_input_check') == 1:
            # if last round was no-input we can assume user hung up
            return 'ABANDONED'
            # return 'NO_INPUT'

        if row.get('no_match_check') == 1:
            return 'NO_MATCH'

        if row.get('operator_check') == 1:
            return 'ESCALATED'

        if row.get('intent_last') == 'req_agent':
            return 'ESCALATED'

        intent: str = row.get('intent_target')
        if isinstance(intent, str) and intent.startswith('head_intent'):
            # probably a handoff to agent?
            return "HEAD_INTENT"

        return None

        # dont trust these filled in values
        # for item in ['escalated', 'contained', 'abandoned']:
        #     if row.get(item):
        #         return item.upper()
        # return 'end_unknown'

    @ typing.no_type_check  # the below is failing typechecking
    def calculate_exit(self):
        """is_start and others that need iteration"""
        rows = []
        last_row: dict = {}
        for (index, row) in self.df.iterrows():
            if (index % 1000 == 0):
                logging.info('row %s/%s', index, len(self.df))

            if row['is_start'] == 1:
                row['page_source'] = 'START'

            if row['is_end'] == 1:
                # we need to look back one row for no-match and hangups
                exit = \
                    self.calc_exit(row) or \
                    self.calc_exit(last_row) or \
                    'UNKNOWN'
                row['page_target'] = exit
                row['exit'] = exit
                last_row['page_target'] = exit  # needed for sankey paths
                # row['completed_check'] == self.completed_check(row)

            # if row['session_id'] != last_row.get('session_id'):
            #     # new convo
            #     row['is_start'] = 1
            #     last_row['is_end'] = 1
            #     last_row['page_target'] = self.calc_exit(row)
            #     last_row['exit'] = self.calc_exit(row)
            #     # TODO - abandoned is on the row-2
            #     # last_row['page_target'] = self.calc_exit(last_row)
            #     # we ALWAYS fill this in as its randomly left out
            #     # row['page'] = 'Start Page'
            #     # row['flow'] = 'Default Start Flow'
            # else:
            #     row['is_start'] = None

            last_row = row
            rows.append(row)
        self.df = pd.DataFrame(rows)
        return self.df

    # def calc_items(self):
        # sessions = self.df.groupby(['session_id'])
        # for _index, session in sessions:
        #     for col in ['page', 'flow']:
        #         # "Series[Any]" has no attribute "ffill"mypy
        #         session[col] = session[col].ffill()  # type: ignore

    # def add_items(self):
    #     sessions = self.df.groupby(['session_id'])
    #     updated = []
    #     for _index, session in sessions:
    #         session.iloc[0]
    #         # session['escalated'] = self.check_operator(session)
    #         # session['no_match'] = self.check_no_match(session)
    #         # session['tc'] = self.guess_tc(session)
    #         updated.append(session)

    #     df = pd.DataFrame(updated)
    #     logging.info('stats \n%s', dumps(updated))
    #     # logging.info('stats \n %s', dumps(df[['driver']]))

    def minimize(self):
        min_df = self.df[self.config['reorder_columns']]
        return min_df

        # updated: List[Dict] = []
        # for _index, session in sessions:
        # session['flow'] = 'BILL'
        # driver = session['intent'].map(ChatStatic.first_driver)
        # logging.info('driver %s', driver)
        # session['driver'] = driver.pop()
        # session['escalated'] = self.check_operator(session)
        # session['no_match'] = self.check_no_match(session)
        # session['tc'] = self.guess_tc(session)
        # updated.append(session)
