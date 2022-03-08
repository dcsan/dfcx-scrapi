"""

see chat_stat - this already does most of this

Calculate paths inc. step buffers from conversations
    take the last line of convo to be the 'step_buffer_path'



"""

import logging
import pandas as pd
import numpy as np
from icecream import ic

from cxutils import biglib
from cxutils import biglib
from cxutils.format.formatter import dumps
from cxutils.digger.chat_log import ChatLog
from cxutils.digger.dig_item import DigItem

ic.configureOutput(prefix='ChatStat |', includeContext=True)


class ChatPath(DigItem):
    """for analyzing calls"""

    def __init__(self, set_name):
        """create new log"""
        super().__init__(set_name)
        self.table_id = biglib.make_table_id('chat_paths')
        self.chat_logs_table = biglib.make_table_id('chat_logs')
        self.chat_logs: ChatLog = None  # other object

    # def load_logs(self):
    #     """load logs"""
    #     self.chat_logs = ChatLog(self.set_name)
    #     self.chat_logs.fetch_bq()
    #     logging.info('fetched chatlogs %s', len(self.chat_logs.df))

    def summarize(self):
        """calculate paths"""
        query = f"""
        SELECT
            count( distinct session) as total,

            concat("p1_", max(page)) as p1,
            concat("p2_", max(page_next)) as p2,

            max(set_name) as set_name,
            max(turn) as t,
            max(set_name) as set_name

            FROM `{self.chat_logs_table}`
            where set_name='{self.set_name}'
            and page_next <> "-"

            group by
                page, page_next, turn

            order by total desc
            """

        data = biglib.query_list(query)
        logging.info('paths: %s', len(data))
        ic(data[0])
        data = ChatPath.remove_dupes(data)
        df = pd.DataFrame(data)
        self.df = df

        self.write_bq(df=df)

    @staticmethod
    def remove_dupes(data):
        data = [item for item in data
                if item['p1'] != [item['p2']]
                ]
        return data
