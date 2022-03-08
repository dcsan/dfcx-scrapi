"""
ChatFunnelSpec
    CUSTOMER description of funnels
"""

import re
from typing import List
import pandas as pd
import logging

from cxutils.format.formatter import dumps
from cxutils import toolbelt
from cxutils.digger.chat_stat import ChatStat
from cxutils.digger.dig_item import DigItem
from cxutils import biglib
from cxutils.digger.chat_static import ChatStatic
from cxutils import gbot
from cxutils import logit
from icecream import ic

ic.configureOutput(prefix='\n---\nChatFunnel |', includeContext=True)


class ChatFunnelSpec(DigItem):
    """Agg Funnels and then post-process"""

    def __init__(self, funnel_name=None):
        super().__init__(funnel_name)
        self.funnel_name = funnel_name
        self.all_funnels = None
        # we use a different sheet from the chat_logs
        # self.init_sheet(cname='chat_funnels')
        # self.chat_logs_table = biglib.make_table_id('chat_funnels')
        self.init_sheet(cname='funnel_defs')
        self.table_id = biglib.make_table_id('chat_funnel_specs')

    def prepare_funnels(self):
        """clean up CUSTOMER funnel defs and split apart steps and write back"""
        joiner = ".*"  # between each step
        wildcard = ['.*']
        # self.init_sheet(cname='funnel_defs')
        df = self.read_gdoc()
        rows = df.to_dict('records')  # iterable
        for idx, row in enumerate(rows):
            row['num'] = idx
            path_start = ChatFunnelSpec.split_steps(row['path_start_sql'])
            # steps_end = ChatFunnelSpec.split_steps(row['full_end_sql'])
            path_end = ChatFunnelSpec.split_steps(row['path_end_sql'])
            path_all = path_start + path_end

            paths = {
                'steps_start': joiner.join(path_start),
                'steps_end': joiner.join(path_end),
                'steps_all': joiner.join(path_all),
            }
            row.update(paths)
            paths2 = {
                'steps_start_rex': '.*' + row['steps_start'] + '.*',
                'steps_end_rex': '.*' + row['steps_end'] + '.*'
            }
            row.update(paths2)
            path_regex = f".*{row['steps_all']}.*"
            row['steps_all_rex'] = path_regex
            del row['path_start_sql']
            del row['path_end_sql']
            del row['full_path_sql']
        ic({'rows': rows})
        df = pd.DataFrame(rows)
        self.write_gdoc(df=df, tabname='funnels_clean')

    @staticmethod
    def split_steps(steps_sql: List[str]) -> List[str]:
        """split up the incoming % in CUSTOMER funnel descriptions"""
        steps_list = steps_sql.split('%')
        steps_trim = [step.replace(";", "") for step in steps_list]
        steps_trim = [step for step in steps_trim if len(step)]
        return steps_trim

    def load_all_funnels(self, sample=None):
        self.all_funnels = self.all_funnels or \
            self.read_gdoc_as_dict(tabname='funnels_clean')
        if sample:
            self.all_funnels = self.all_funnels[:sample]
        return self.all_funnels

    def get_one_funnel(self, funnel_name):
        self.load_all_funnels()
        self.funnel = toolbelt.find_one(self.all_funnels, 'cname', funnel_name)

        logit.obj('funnel.start_path', self.funnel)
        return self.funnel

    def match_path(self, part: str, convo_set, funnel):
        count = 0
        # easypath = f'.*{path}.*'
        try:
            pathstr = funnel[part]
            rex = re.compile(pathstr)
            rows = convo_set.rows
            # ic('rows in convo', len(rows))
            for convo in rows:
                full_path = convo.get('step_buffer_path')
                if full_path:
                    if re.match(rex, full_path):
                        # print('found', full_path, part)
                        count += 1
                    # else:
                        # ic('no match', rex, part, pathstr, full_path)
        except TypeError:
            logging.error('failed rex part [%s] in funnel %s', part, funnel)
            logging.error('convo %s', dumps(convo))
            # continue?
            # raise err
            # return 0

        return count

    def check_one_funnel(self, funnel, convo_set=None):
        parts = {
            'funnel_name': funnel['cname'],
            'steps_start': self.match_path('steps_start_rex', convo_set, funnel),
            'steps_end': self.match_path('steps_end_rex', convo_set, funnel),
            'steps_full': self.match_path('steps_all_rex', convo_set, funnel),
            'steps_start_rex': funnel['steps_start_rex'],
            'steps_end_rex': funnel['steps_end_rex'],
            'steps_all_rex': funnel['steps_all_rex']
        }
        if parts['steps_start'] == 0:
            completion = 0
        else:
            completion = parts['steps_full'] / parts['steps_start']
            completion = min(completion, 1)  # cannot be more than 100%
        parts['completion'] = completion
        ic('parts', parts)
        return parts

    def check_all_funnels(self, set_name, sample=None):
        funnels = self.load_all_funnels(sample=sample)
        results = []
        convo_set = ChatStat(set_name=set_name)
        convo_set.load_bq()
        total = len(funnels)
        for idx, funnel in enumerate(funnels):
            if idx % 500 == 0:
                gbot.notify(f'`{idx}/{total}` funnels ')
            result = self.check_one_funnel(
                convo_set=convo_set,
                funnel=funnel)

            results.append(result)
        ic(results)
        df = pd.DataFrame(results)
        df['set_name'] = set_name

        table_name = 'funnel_stats'
        where = f'set_name="{set_name}" '
        biglib.delete(table_name=table_name, where=where)
        biglib.insert_df(df, table_name=table_name)
        tabname = f'{set_name}_cust_funnels'
        self.write_gdoc(df=df, cname=set_name, tabname=tabname)
