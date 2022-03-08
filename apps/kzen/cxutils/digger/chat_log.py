"""
Loading chatlogs from provided call logs
line by line / turn by turn raw logs for each chat
preparing chatlogs so we can do aggregations for conversations

we use integers for booleans to make it easier to do math later

    renamed (normalized):
        utterance
        page
        intent

    assigned:
        sprint = number
        set_name = assigned
        xp_name = experiment
        is_xp = 1/0 for experiment

    calculated:
        turn - depth in chat
        driver
        flow
        no_match = was a nomatch?
        re_match = if nomatch we rematch on start flow using an agent
        operator = operator intent
        is_disambig = is a disambiguation?
        tc_guess - simple guess
        tc_label - for DDs later
        page_from, page_next = linked pages in same convo


    renames some fields from inputs to normalize field names
    cleans up timestamp from text to ts(timestamp) and ds(date)
    page_from and page_next - calculated per page

"""
import re

from executing.executing import statement_containing_node
from cxutils.digger.chat_stat import ChatStat
import logging
from typing import Dict, List  # , Literal
import pandas as pd
import numpy as np
from icecream import ic
# import math

from cxutils.digger.dig_item import DigItem
from cxutils.digger.chat_static import ChatStatic
from cxutils import biglib
from cxutils import gbot
from cxutils.dclib import dclib
# from cxutils.sheeter import Sheeter
from cxutils.format.formatter import dumps


SESSION_STUB = "projects/CUSTOMER-it-pr-pp4v-ppv4-0/locations/global/agents/65faecda-1d57-4816-8d06-134d0b18e755/environments"

# classify as non-matched for later filling
NO_MATCH_INTENTS = [
    'No Match',
    # 'No Input',
    'Parameter Filling',
    None,
    ''
]


# columns we add into the raw logs
# also used to reorder the columns
CALCULATED_COLUMNS = [
    'operator',
    'fallout',
    'thanks',   # thanks = TC true indicator
    'is_hid',
    'tc_estimate',  # estimate of task completion
    'no_input',
    'no_match',
    'is_xp',
    'is_bill',
    'escalated',

    'turn',  # depth
    'convo_id',  # index of convos
    'start_flow',  # start of input
    'review',


    'utterance',
    'intent_page',
    'intent_detail',
    'reply',

    'flow',     # end of transitions
    'intent',   # raw intent
    're_match',  # matching when there was a no-match
    'page',
    'driver',   # important pages

    'steps',
    'transitions',

    'page_from',
    'page_next',
    'intent_from',  # calc flows
    'intent_next',  # calc flows
    'start',    # turn0
    'set_name',  # added
    'xp_name',       # which experiment


]

# COLUMN_ORDER: List[str] = [
#     'escalated',
#     'operator',
#     'thanks',
#     'tc_guess'
# ]

RENAME_COLS = {
    'Session ID': 'session',
    'Session Facts Session ID': 'session',

    'Session Facts Avaya call ID': 'avaya',
    'Avaya call ID': 'avaya',

    'Receive Timestamp Time': 'timestamp',
    'Dialogflow Requests Receive Timestamp Time': 'timestamp',

    'Human Message': 'utterance',
    'Query Result Human Message': 'utterance',


    'All Bot Messages': 'reply',
    'Messages All Bot Messages': 'reply',

    'Turn Intent': 'intent',
    'Query Result Intent Display Name': 'intent',

    'Start Page': 'start_page',
    'Step Details Start Page': 'start_page',

    'Current Page Display Name': 'page',
    'Query Result Current Page Display Name': 'page',

    'Session Turn Number': 'turn',
    'Voice Data Turn Facts Session Turn Number': 'turn',

    'All Steps': 'steps',
    'Step Details All Steps': 'steps',

    'Query Result: Diagnostic Info Step Buffer': 'step_buffer',
    'Step Buffer': 'step_buffer',

    'All Transitions': 'transitions',
    'Step Details All Transitions': 'transitions',

    # last as they may already exist
    'user_request': 'utterance',
    'intent_display_name': 'intent',
    'agent': 'reply',  # in case old ones

    'Messages List of all Audio Messages': 'audio',

}


OPERATOR_REPLIES = [
    # "Let me get you to someone who can help",
    # "Please hold while I connect you to someone",
    # "Let me transfer you to someone who can help",
    # "Please hold while I connect you to an agent",
    # "connect you to someone",
    "someone who can help",
    "transfer you to someone",
    "connect you to an agent",
    "Please hold while I connect you",
    "Let me get you to someone who can help."
]

# transitions that should register an escalation
ESC_TRANSITIONS = [
    # TRBL
    # 'page(TRBL::(Escalate) Troubleshooting)'
    '(Escalate) Troubleshooting)'
]

# some things a user can say to escalate
# ESCALATION_UTTERANCES = [
#     "dtmf_digits_0"
# ]

# if 'parameter filling' these guess if user said operator
OPERATOR_KEYWORDS = [
    'operator',
    'representative',
    'agent',
    "dtmf_digits_0",
    'customer service',
    'tech support',
    'support'
]

THANKS_MESSAGES = [
    "Thanks for calling"
]

# pages included in experiments
XP_PAGES = [
    'meena_dis'
]

XP_STEP_BUFS = ['TCFE']

# XP_STEP_BUFS = [
#     {
#         'buf': 'TCFE',
#         'xp': 'meena'
#     },
#     {
#         'buf': 'xxx',
#         'xp': 'yyy'
#     }
# ]


class ChatLog(DigItem):
    """for analyzing calls"""
    version = 6

    def __init__(self, set_name):
        """create new log"""
        super().__init__(set_name)
        self.table_id = biglib.make_table_id('chat_logs')
        self.df: pd.DataFrame = None
        ic('__init__ ChatLog v', ChatLog.version)

    def process(self, update_gdoc=False):
        '''do pipeline of cleanups'''

        # self.remove_blank_inputs()
        self.fix_columns()
        self.clean_session()
        self.sort_rows()
        self.basic_cleanup()
        self.fix_timestamp()
        self.guess_basics()
        self.set_meta(opts={})

        if update_gdoc:
            self.write_gdoc(tabname=f'{self.set_name}_clean')

        # self.mark_start('head_intent.bill_explain_incorrect')
        return self.df
        # self.calc_paths(write_doc=True)
        # self.doc.write_tab(self.tabname, self.df)

    def fix_columns(self):
        self.df = dclib.rename_columns(self.df, RENAME_COLS)
        self.df = dclib.add_columns(self.df, CALCULATED_COLUMNS)
        self.df = dclib.reorder_columns(self.df, CALCULATED_COLUMNS)
        self.df['turn'] = self.df['turn'].astype(int)

    def light_clean(self):
        """simple process on already cleaned logs
        useful when doing aggregation"""
        self.fix_columns()
        # self.rename_columns()
        # self.reorder_columns(CALCULATED_COLUMNS)
        return self.df

    def set_meta(self, opts={}):
        """add some metadata columns to the whole log"""
        for key, val in opts.items():
            self.df[key] = val
        self.df['set_name'] = self.set_name  # for BQ
        self.df['xp'] = opts.get('xp_name')

    def fix_timestamp(self):
        """supplied timetstamps are in text format and such a mess
        so we clean up to stop BQ choking on import
        """
        try:
            ts = self.df['timestamp'].apply(biglib.fix_timestamp)
            self.df['dt'] = ts  # BQ datetime type
            self.df['ts'] = ts  # BQ timestamp
        except KeyError as err:
            logging.error('no timestamp in table [%s]', self.set_name)
        # ic('fix_timestamp ', len(self.df))
        # ic('df.dt ', self.df[['dt']])
        return self.df

    # def rename_columns(self):
    #     """logs and DB field names don't match up"""
        # TODO - check if col exists? so we don't replace agent with empty reply
        # self.df.rename(columns=RENAME_COLS, inplace=True)
        # self.df['set_name'] = self.set_name  # for BQ
        # self.df['xp'] = None
        # # add some extra columns
        # for col in CALCULATED_COLUMNS:
        #     if col not in self.df.columns:
        #         # create the column but add generic data type
        #         self.df[col] = None

        # # drop those with empty column names
        # if "" in self.df.columns:
        #     self.df.drop([""], axis=1, inplace=True)

        # ic('renamed columns: ', dumps(self.df.columns))

    def clean_session(self):
        '''remove extra fat from columns'''
        junk = SESSION_STUB
        self.df['convo'] = self.df['session'].map(lambda x: x.lstrip(junk))

    def basic_cleanup(self):
        """replace empty items with [None] etc"""
        empties = {"": "[None]", np.nan: "[NaN]"}
        # quotes = {'"': ''}
        self.df["utterance"].replace(empties, inplace=True)
        self.df['reply'].replace(empties, inplace=True)
        self.df['step_buffer'] = self.df['step_buffer'].str.replace('"', '')

    def sort_rows(self):
        """data from looker is not sorted SOB"""
        self.df = self.df.sort_values(by=['session', 'turn'])

    # def remove_blank_inputs(self):
    #     '''remove no user input - update we dont do this now so we can capture these'''
    #     # have to convert to use dropna
    #     self.df['utterance'].replace('', np.nan, inplace=True)
    #     self.df.dropna(subset=['utterance'], inplace=True)
    #     print('removed blanks:', self.df.shape)

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

    @staticmethod
    def guess_yes_no(text: str):
        #  -> Literal['confirmation.yes', 'confirmation.no', None]
        '''guess basic intents to save queries to DFCX'''
        text = text.strip().lower()
        if text in ['yes', 'okay']:
            return 'confirmation.yes'
        elif text == 'no':
            return 'confirmation.no'
        return None

    @staticmethod
    def is_operator(row) -> int:
        """asked for operator
            Session ended with dtmf_digits_0
            'Parameter filling' intent with "Operator/Representative" as utterance
        """
        if row['re_match'] == 'Operator':
            return 1
        if row['intent'] == 'Operator':
            return 1
        utterance: str = row.get('utterance').lower()
        if row['intent'] == 'Parameter Filling':
            if utterance in OPERATOR_KEYWORDS:
                return 1  # this would just be 'param filling'
            for word in OPERATOR_KEYWORDS:
                # this might be a bit overaggressive
                # if just operator keyword appears
                if word in utterance.lower():
                    return 1
        return 0

    @staticmethod
    def did_escalate(row) -> int:
        """session DID escalate.
            asking for operator often goes to disambig
            but here we detect based on agent response if its really escalation
            Agent ended session with one of:
                “Let me get you to someone who can help”
                “Please hold while I connect you to someone”
                “Let me transfer you to someone who can help”
                “Please hold while I connect you to an agent”
        """
        for test in OPERATOR_REPLIES:
            # breakpoint()
            reply = row.get('reply')
            if reply and test in reply:
                return 1
        for test in ESC_TRANSITIONS:
            if test in row['transitions']:
                return 1
        return 0

    @staticmethod
    def is_fallout(row) -> int:
        """session fallout = escalation + error"""
        if row['escalated'] == 1:
            return 1
        return 0

    @staticmethod
    def fill_re_match(row) -> str:
        """take the intent, or else calculate it"""
        re_match = None
        intent = row.get('intent')

        if intent not in NO_MATCH_INTENTS:
            return intent

        if ChatLog.is_operator(row):
            return 'Operator'

        re_match = ChatLog.guess_yes_no(row['utterance'])
        if re_match:
            return re_match

        # logging.info(
        #     'cannot rematch %s [%s] | rematch:%s',
        #     intent, row['utterance'], re_match)

        # TODO consider rematch against StartFlow
        # but this will cover design problems with agent

        # return original intent, could be NoMatch etc.
        return intent

    @staticmethod
    def is_no_match(row) -> int:
        """simple guess for no match"""
        intent = row.get('intent')
        if intent == 'No Match':
            return 1
        return 0

    @staticmethod
    def is_no_input(row) -> int:
        """simple guess for no match"""
        intent = row.get('intent')
        if intent == 'No Input':
            return 1
        return 0

    # @staticmethod
    # def is_end(row) -> int:
    #     """last row"""
    #     intent = row.get('intent')
    #     if intent == 'No Input':
    #         return 1
    #     return 0

    @staticmethod
    def tc_estimate(row):
        """basic heuristic guess for task completion"""
        if row['is_hid'] == 1:
            return 1
        if row['thanks'] == 1:
            return 1
        if row['escalated'] == 1:
            return 0
        if row['operator'] == 1:
            return 0.5  # going badly but not escalated yet
        return None  # unknown so empty for calculations

    @staticmethod
    def is_thanks(row) -> int:
        """used to define a happy path"""
        reply = row.get('reply')
        if reply:
            for msg in THANKS_MESSAGES:
                if msg in reply:
                    return 1
        return 0

    @staticmethod
    def is_start(row) -> int:
        """used to define a happy path"""
        turn = row.get('turn')
        if turn == 1 or turn == '1':
            return 1
        return 0

    @staticmethod
    def is_xp_row(row) -> int:
        """is this part of an experiment"""
        page = row.get('page')
        if page in XP_PAGES:
            return 1
        step_bufffers = row.get('step_buffer')
        if step_bufffers:
            for buf in XP_STEP_BUFS:
                if buf in step_bufffers:
                    return 1
        return 0

    @staticmethod
    def is_bill(row):
        if row['page'] in ChatStatic.bill_pages:
            return 1
        return 0

    @staticmethod
    def is_hid(row):
        step_id = row.get('step_buffer')
        if step_id is None:
            # logging.info('null step buffer in row %s', row)
            # 0624 data does NOT have this value >.<
            return None
        if step_id.endswith('NUCY'):
            return 1
        # if row['intent'].startswith('head_intent'):
        #     return 1
        return 0

    @staticmethod
    def get_flow_from_step(info: str):
        parts: List[str] = info.split('::')
        if parts:
            return parts[0]
        return None

    @staticmethod
    def intent_page(row):
        """get the intent>page path"""
        item = row['re_match'] + " > " + row['page']
        return item

    @staticmethod
    def get_step_parts(row):
        # page(Default Start Flow::Start Page)|intent(Default Welcome Intent)|webhook(status=OK, latency=56)|page(Default Start Flow::Flow Transition)|condition(true)|page(Default Start Flow::HID DTMF AccType filter)
        trans = row.get('steps')
        if not trans:
            # need to fix source data
            # print('warning - no `steps` in row')
            return
        start: str = trans.split('|')[0]
        end: str = trans.split('|')[-1]
        parts = {
            'start_flow': ChatLog.get_flow_from_step(start),
            'end_flow': ChatLog.get_flow_from_step(end),
        }
        return parts

    def guess_basics(self):
        '''update `actual` and guess yes/no columns for empties'''

        gbot.notify('guess_basics')
        convo_count = 0
        self.df['convo_id'] = 0  # create column

        updated = []
        for index, row in self.df.iterrows():
            row['start'] = ChatLog.is_start(row)
            if row['start'] == 1:
                convo_count += 1
                row['convo_id'] = convo_count
            else:
                row['convo_id'] = None  # empty for easy skipping

            parts = ChatLog.get_step_parts(row)
            if parts:
                row['start_flow'] = parts['start_flow']
                row['flow'] = parts['end_flow']

            # order is important
            row['re_match'] = ChatLog.fill_re_match(row)
            row['no_match'] = ChatLog.is_no_match(row)
            row['no_input'] = ChatLog.is_no_input(row)
            row['tc_estimate'] = ChatLog.tc_estimate(row)
            row['thanks'] = ChatLog.is_thanks(row)
            row['is_hid'] = ChatLog.is_hid(row)
            row['is_bill'] = ChatLog.is_bill(row)
            row['operator'] = ChatLog.is_operator(row)
            row['escalated'] = ChatLog.did_escalate(row)
            row['fallout'] = ChatLog.is_fallout(row)

            row['intent_detail'] = ChatStatic.is_intent_detail(row['re_match'])
            row['driver'] = ChatStatic.first_driver(row['intent'])

            row['is_xp'] = ChatLog.is_xp_row(row)
            row['intent_page'] = ChatLog.intent_page(row)

            if (index % 5000 == 0):
                gbot.notify(f'{index}/{len(self.df)} guess_basics')
            updated.append(row)

        updated = ChatLog.calc_page_links(updated)
        self.df = pd.DataFrame(updated)

    @staticmethod
    def calc_page_links(convo_lines):
        """calc next and prev pages by running over the whole list once
        args:
            convo_lines - the whole table eg 20k rows
        """
        gbot.notify('calc_page_links')
        updated = []
        for idx, line in enumerate(convo_lines):
            line['is_end'] = 0
            if idx == len(convo_lines) - 1:
                # last line of whole set
                line['is_end'] = 1

            else:
                line['is_end'] = 0  # default
                next_line = convo_lines[idx + 1]
                if next_line['session'] == line['session']:
                    line['page_next'] = next_line.get('page')
                    line['intent_next'] = next_line.get('intent')
                else:
                    # new convo
                    line['is_end'] = 1
                    line['page_next'] = 'EndSession'
                    line['intent_next'] = 'EndSession'

            updated.append(line)

            # ic(idx, line)

        return updated
