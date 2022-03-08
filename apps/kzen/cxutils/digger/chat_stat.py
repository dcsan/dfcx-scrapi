"""
Chat Stats
    aggregating chat_logs
    group by session

    summarize:
        pages, rev_pages
        step_buffer_path - final step buffer

    save to chat_stats table

    TODO
        flows based on page:flow mapping table

"""

from typing import Dict, List
# from config import configlib
import pandas as pd
import logging
from cxutils.digger.dig_item import DigItem
from cxutils import biglib
from cxutils.digger.chat_static import ChatStatic
from cxutils import gbot
from cxutils.dclib import dclib
from icecream import ic

ic.configureOutput(prefix='ChatStat |', includeContext=True)

COLUMN_ORDER = [
    'operator',
    'fallout',
    'thanks',   # thanks = TC true indicator
    'tc_guess',  # estimate of task completion
    'is_hid',
    'is_xp',
    'is_bill',
    'no_input_count',
    'no_input_rate',
    'no_match_count',
    'no_match_rate',

    'utterances',
    'intent_page',
    'replies',

    'intent_stated',
    'intent_detected',
    'tc',

    'is_dropoff',
    'escalated',
    'true_esc',
    'review',

    'intent_detail',
    'intent_detail_flag',
    'duration',

    'session',
    'set_name', 'xp_name',

    'p0', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6',
    'rp0', 'rp1', 'rp2', 'rp3', 'rp4', 'rp5', 'rp6',

]

# items we split as newline \n fields from string_agg's
newline_fields = [
    # 'key_steps',
    'intents',
    'replies',
    'utterances',
    'rev_intents',
    'pages', 'rev_pages',
    'intents', 'rev_intents',
    'intent_page',
    're_matches',
    'flows'
]


class ChatStat(DigItem):
    """Agg ChatLogs and then post-process"""

    def __init__(self, set_name):
        super().__init__(set_name)
        self.chat_logs_table = biglib.make_table_id('chat_logs')
        self.table_id = biglib.make_table_id('chat_stats')
        self.rows = None  # when loaded from BQ

    def summarize(self, update_gdoc=False, limit=5000):
        """aggregate and then cleanup"""
        query = f'''
            select
            session,
            max(turn) as turns,
            max(set_name) as set_name,
            max(xp_name) as xp_name,
            max(is_xp) as is_xp,

            # min(ts) as ts,
            # min(dt) as dt,

            max(operator) as operator,
            max(escalated) as escalated,
            max(is_hid) as is_hid,
            max(is_bill) as is_bill,
            sum(no_match) as no_match_count,
            avg(no_match) as no_match_rate,
            max(tc_guess) as tc_guess,
            avg(tc_estimate) as tc_estimate,
            sum(no_input) as no_input_count,
            avg(no_input) as no_input_rate,
            max(fallout) as fallout,
            max(thanks) as thanks,
            max(intent_detail) as intent_detail,

            STRING_AGG( page order by turn asc) as pages,
            STRING_AGG(page ORDER BY turn Desc) AS rev_pages,

            STRING_AGG(re_match ORDER BY turn Asc) AS intents,
            STRING_AGG(re_match ORDER BY turn Desc) AS rev_intents,

            STRING_AGG(driver ORDER BY turn ASC) AS drivers,
            STRING_AGG(driver ORDER BY turn Desc) AS rev_drivers,

            STRING_AGG(flow ORDER BY turn Asc) AS flows,

            STRING_AGG(
                utterance
                order by turn asc
            ) as utterances,

            STRING_AGG(
                re_match
                order by turn asc
            ) as re_matches,

            STRING_AGG(
                reply
                order by turn asc
            ) as replies,

            string_agg(
                intent_page
                order by turn asc
            ) as intent_page,

            ARRAY_AGG(
                start_page order by turn asc
            )[OFFSET(0)]
            AS start_page,

            ARRAY_AGG(
                page order by turn desc
            )[OFFSET(0)]
            AS exit_page,

            ARRAY_AGG(
                flow order by turn desc
            )[OFFSET(0)]
            AS exit_flow,

            ARRAY_AGG(
                transitions order by turn desc
            )[OFFSET(0)]
            AS transitions,

            # duration calc
            DATE_DIFF(max(ts), min(ts), SECOND) as duration,

            # short calls are < 45 secs
            CASE
                WHEN DATE_DIFF(max(ts), min(ts), SECOND) < 45
                THEN 1 ELSE 0
            END as is_short,

            CASE
                WHEN max(intent_detail) IS NOT NULL
                THEN 1 ELSE 0
            END as intent_detail_flag,

            # last item (order desc) for step_buffer
            max(step_buffer) as max_buffer_path,
            ARRAY_AGG(
                step_buffer order by turn desc
            )[OFFSET(0)]
            AS step_buffer_path,

            from `{self.chat_logs_table}`
            where set_name = '{self.set_name}'

            group by session
            order by session
            # order by dt asc

            # order by session
            # order by max(turn) desc
            '''
        rows = biglib.query_list(query)
        logging.info('length of stats %s', len(rows))
        rows = ChatStat.add_exit_items(rows)
        # rows = ChatStat.clean_paths(rows)
        rows = ChatStat.process_rows(rows)
        ic('first', rows[0])
        df = pd.DataFrame(rows)
        if limit:
            df = df.head(limit)
        self.df = df
        self.df = dclib.reorder_columns(df, COLUMN_ORDER)
        self.write_bq(df=df)
        if update_gdoc:
            self.write_gdoc(tabname=f'{self.set_name}_stats')
        return self.df

    # def get_step_buffer(self):
    #     """select the last row as the step buffer"""
        # query = f'''SELECT
        #     session,
        #     max(turn) as turns,

        #     ARRAY_AGG(step_buffer)[OFFSET(0)] AS path
        #     from `{self.chat_logs_table}`
        #     where set_name = '{self.set_name}'
        #     GROUP BY session
        #     order by max(turn) desc
    #     '''
    #     data = biglib.query_list(query)

    @staticmethod
    def get_last_part(items, reject_items, offset=0):
        """get last item in a list with filter"""
        if not items:
            return None
        items = items.split(',')
        if items and len(items) > offset:
            items = [item for item in items if item not in reject_items]
            if items and len(items) > offset:
                items.reverse()  # in place, sigh
                return items[offset]
        return None  # no items

    # @ staticmethod
    # def clean_paths(agg_data: List[Dict]):
    #     """clean up items and remove quote marks in paths"""
    #     for _idx, convo in enumerate(agg_data):
    #         path = convo['step_buffer_path']
    #         if path:
    #             path = path.strip('"')
    #             convo['step_buffer_path'] = path
    #         if convo.get('key_steps'):
    #             # from array concat
    #             convo['key_steps'] = convo.get('key_steps').replace(",", "")
    #         if convo.get('utterances'):
    #             # from array concat
    #             convo['utterances'] = convo.get('utterances').replace(",", "")
    #     return agg_data

    @staticmethod
    def add_exit_items(agg_data):
        """calc exit pages and drivers"""
        for idx, convo in enumerate(agg_data):
            convo['exit_page'] = ChatStat.get_last_part(
                convo['pages'], ChatStatic.filter_pages, offset=0)

            convo['exit_intent'] = ChatStat.get_last_part(
                convo['intents'], ChatStatic.ignore_drivers)

            convo['exit_driver'] = ChatStat.get_last_part(
                convo['drivers'], ChatStatic.ignore_drivers)

            if idx % 1000 == 0:
                gbot.notify(f'{idx}/{len(agg_data)} calc exit items')

        return agg_data

    @staticmethod
    def add_newlines(row):
        for field in newline_fields:
            line = row.get(field)
            if not line:
                logging.info('no value in field %s', field)
                continue
            items = line.split(',')  # BQ array agg separator
            row[field] = '\n'.join(items)
        return row

    @staticmethod
    def process_rows(rows):
        logging.info('process %s rows', len(rows))
        newrows = []
        for count, row in enumerate(rows):
            if count % 500 == 0:
                logging.info('row %s/%s', count, len(rows))
            newrow = ChatStat.add_page_steps(row)
            newrow = ChatStat.add_newlines(newrow)
            newrow = ChatStat.dedupe_pages(newrow)
            newrow = ChatStat.calc_duration(newrow)
            # newrow = ChatStat.check_intent_detail(newrow)
            newrows.append(newrow)
        return newrows

    @staticmethod
    def calc_duration(row):
        """calc ts max and min"""
        return row

    @staticmethod
    def check_intent_detail(row):
        """add a 1/0 value if there is an intent_detail for avg calcs"""
        if row.get('intent_detail'):
            row['intent_detail_flag'] = 1
        else:
            row['intent_detail_flag'] = 0
        return row

    @staticmethod
    def add_page_steps(row):
        """add p0,p1,p2 and reverse rp0,rp1,rp2 fields for path calculations"""
        pages = row['pages'].split(',')
        max_page = min(len(pages), 6)
        for c in range(0, max_page):
            row[f'p{c}'] = pages[c]
            backc = (max_page - 1) - c
            row[f'rp{c}'] = pages[backc]
        return row

    def trim_db(self, row):
        '''truncate to only 5k rows for this set to make comparisons easier in dashboard'''
        rows = self.load_bq(limit=5000)

    def load_bq(self, limit=None):
        """load from bigQuery"""
        query = f"""select * from {self.table_id}
        where set_name='{self.set_name}' """
        if limit:
            query = f'{query} LIMIT {limit} '
        self.rows = biglib.query_list(query)
        return self.rows

    @staticmethod
    def dedupe_pages(row):
        """remove repeat pages in list for easier analysis"""
        new_pages = []
        pages = row['pages'].split(',')
        last_page = None
        for page in pages:
            if page != last_page:
                new_pages.append(page)
            last_page = page
        row['pages_dedupe'] = '\n'.join(new_pages)
        return row

    # def dedupe(self):
    #     rows = self.load_bq()
    #     sessions = [c['session'] for c in rows]
    #     uniq = set(sessions)
    #     ic('dedupe', len(uniq), len(sessions))
    #     for sessid in uniq:

    #     convos = [c for c in rows if c['session'] in uniq]
    #     df = pd.DataFrame(convos)
    #     self.df = dclib.reorder_columns(df, COLUMN_ORDER)
    #     # self.write_gdoc(tabname=f'{self.set_name}_uniq')
