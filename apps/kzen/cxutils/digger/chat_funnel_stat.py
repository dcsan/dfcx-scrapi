"""
ChatFunnelSpec
    CUSTOMER description of funnels
"""

from typing import List
import pandas as pd
import logging
from cxutils.digger.dig_item import DigItem
from cxutils import biglib
from cxutils.digger.chat_static import ChatStatic
from cxutils import gbot
from icecream import ic

ic.configureOutput(prefix='ChatFunnel |', includeContext=True)


class ChatFunnelStat(DigItem):
    """Agg Funnels and then post-process"""

    def __init__(self, funnel_name=None):
        super().__init__(funnel_name)
        self.funnel_name = funnel_name
        # we use a different sheet from the chat_logs
        # self.init_sheet(cname='chat_funnels')
        # self.chat_logs_table = biglib.make_table_id('chat_funnels')
        self.table_id = biglib.make_table_id('chat_funnel_stats')

    def prepare_funnels(self):
        """clean up CUSTOMER funnel defs and split apart steps and write back"""
        separator = ";"  # not a regex char
        self.init_sheet(cname='funnel_defs')
        df = self.read_gdoc()
        rows = df.to_dict('records')  # iterable
        for idx, row in enumerate(rows):
            row['num'] = idx
            steps_start = ChatFunnelSpec.split_steps(row['path_start_sql'])
            steps_end = ChatFunnelSpec.split_steps(row['path_end_sql'])
            steps_mid = '.*'
            steps_all = steps_start + [steps_mid] + steps_end
            row['steps_start'] = separator.join(steps_start)
            row['steps_end'] = separator.join(steps_end)
            row['steps_all'] = separator.join(steps_all)
            del row['path_start_sql']
            del row['path_end_sql']
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
