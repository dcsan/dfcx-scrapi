"""
Simple version of funnels
"""

from typing import Dict, List
from config import configlib
import pandas as pd
import logging
from cxutils.digger.dig_item import DigItem
from cxutils import biglib
from cxutils.digger.chat_static import ChatStatic
from cxutils import gbot
from cxutils import toolbelt
from icecream import IceCreamDebugger

from cxutils.dclib import dclib

ic = IceCreamDebugger()
ic.configureOutput(prefix='SimpleFunnel |', includeContext=False)

ACTIVE_FLAG = 1  # enable quick focus on different funnel sets


class SimpleFunnel(DigItem):
    """Agg ChatLogs and then post-process"""

    def __init__(self, chat_set, funnel_set='basic', get_gdoc=True):
        super().__init__(set_name=funnel_set)
        self.chat_set = chat_set
        self.funnel_specs_table = biglib.make_table_id('simple_funnels')
        self.funnel_stats_table = biglib.make_table_id('simple_funnel_stats')
        self.table_id = self.funnel_specs_table  # needed for DigItem

        self.funnels = None
        self.funnel_set = funnel_set
        self.init_sheet(cname='simple_funnels', tabname='simple_funnels')
        if get_gdoc:
            self.load_funnel_specs_doc()

    def load_funnel_specs_doc(self):
        """reload funnel specs from gdoc"""
        rows = self.read_gdoc_as_dict(cname='simple_funnels')
        rows = [row for row in rows if row.get('cname') is not None]

        # sometimes filter here so we dont get extra specs
        # rows = dclib.filter_list(rows, 'set_name', self.funnel_set)

        df = pd.DataFrame(rows)
        # dangerous query of the day so make sure to set table_name here
        sf_table = biglib.make_table_id('simple_funnels')
        biglib.query(f'delete from {sf_table} where TRUE')
        self.write_bq(df, table_id=self.funnel_specs_table, delete_first=False)
        logging.info('wrote simple_funnel specs to bq %s', len(df))

    def load_funnels_cache(self, cname=None):
        if self.funnels is not None:
            return self.funnels
        if cname:
            self.cname = cname
        query = f"""
            select * from {self.funnel_specs_table}
            where set_name='{self.funnel_set}'
            order by row, cname, turn
        """
        funnels: List[Dict] = biglib.query_list(query)
        self.funnels = SimpleFunnel.clean_steps(funnels, flag=ACTIVE_FLAG)
        self.funnels = dclib.filter_list(funnels, 'set_name', self.funnel_set)
        return self.funnels

    @staticmethod
    def clean_steps(funnel_steps, flag=1):
        """get all steps for enabled funnels"""
        funnel_steps = [step for step in funnel_steps
                        if step['enabled'] == flag
                        and step['cname'] is not None
                        and step['cname'] != ""
                        ]
        ic('total funnel steps', len(funnel_steps))
        return funnel_steps

    def check_all_funnels(self, reset_first=True, funnel_set=None):
        """check ALL funnels that are active"""
        if reset_first:
            self.reset_all_stats()
        self.load_funnels_cache(funnel_set)
        query = f"select distinct(cname) from {self.funnel_specs_table} where cname is not NULL"
        if funnel_set:
            query = f'{query} and set_name="{funnel_set}" '
        cnames = biglib.query_list(query)
        ic('funnel cnames', cnames)
        all_results = []
        for item in cnames:
            cname = item['cname']
            if not cname:
                continue  # empty row
            set_results = self.check_one_funnel(cname)
            for result in set_results:
                all_results.append(result)

        ic('all_results', len(all_results))
        self.write_all_results(all_results)

    def reset_all_stats(self):
        where = f"chat_set='{self.chat_set}' "
        biglib.delete(where=where, table_id=self.funnel_stats_table)

    def reset_one_stats(self, cname):
        # where = f"chat_set='{self.chat_set}' and funnel_set='{self.set_name}' "
        where = f"chat_set='{self.chat_set}' and cname='{cname}' "
        biglib.delete(where=where, table_id=self.funnel_stats_table)

    def get_one_funnel_steps(self, cname) -> List[dict]:
        """gets the list of steps that make up a funnel"""
        self.load_funnels_cache()

        # def picker(step):
        #     if step['cname'] == cname and step['set_name'] == self.set_name:
        #         return True
        # funnel_steps = filter(picker, self.funnels)
        # return list(funnel_steps)
        funnel_steps = [step for step in self.funnels
                        if step['cname'] == cname and
                        step['set_name'] == self.set_name
                        ]
        if len(funnel_steps) == 0:
            logging.info('no funnel steps for cname: [%s]', cname)
            return []  # None
        return funnel_steps

    def check_one_funnel(self, cname, save=False) -> List[dict]:
        """check all funnel steps against chat"""
        funnel_steps = self.get_one_funnel_steps(cname=cname)
        if not funnel_steps:
            return []
        events = [step['event'].strip() for step in funnel_steps]
        results = []
        last_count = 0
        first_count = None

        for turn, line in enumerate(funnel_steps):
            until = events[0:turn+1]
            # until = [f'.*({u})' for u in until]
            # rex = ".*".join(until)
            # rex = "\\n".join(until)
            pattern = '.*'.join(until)
            # book-ends - results in extra .* but...
            pattern = f'.*{pattern}.*'
            # query = f'.*{rex}.*'  # start and end
            # query = query.replace('.*', '%')  # for 'like'
            # line['rex'] = pattern
            step_stats = self.check_chats(pattern)
            count = step_stats['total']
            if turn == 0:
                cvr = 1
                cvr_top = 1
                first_count = count
            else:
                cvr = (1.0 * count) / max(last_count, 1)
                cvr_top = (1.0 * count) / max(first_count, 1)
            last_count = count
            result = {
                'chat_set': self.chat_set,
                'funnel_set': self.set_name,
                'cname': cname,
                'count': count,
                'turn': turn,
                'cvr': cvr,
                'cvr_top': cvr_top
            }
            result.update(step_stats)
            results.append(result)
        if save:
            self.write_one_result(results, cname=cname)
        return results

    def check_chats(self, pattern):
        chat_stats_table = biglib.make_table_id('chat_stats')
        # and intent_page like '{query}'

# esc_total:FLOAT,
# esc_rate:FLOAT,
# turns_total:FLOAT,
# turns_avg:FLOAT,
# no_input_rate:FLOAT,
# no_match_rate:FLOAT,
# no_input_total:FLOAT,
# no_match_total:FLOAT,
# utterances_max_len:FLOAT

        rex = f'(?sim){pattern}'  # s = .*/n matching gim

        query = f"""
            select
            count(*) as total,
            sum(escalated) as esc_total,
            avg(escalated) as esc_rate,
            sum(turns) as turns_total,
            avg(turns) as turns_avg,
            avg(no_input_rate) as no_input_rate,
            avg(no_match_rate) as no_match_rate,
            sum(no_input_count) as no_input_total,
            sum(no_match_count) as no_match_total,
            sum(operator) as operator_total,
            avg(operator) as operator_rate,
            length(max(utterances)) as utterances_max_len
            from {chat_stats_table}
            where set_name='{self.chat_set}'
            and regexp_contains(intent_page, '{rex}')
            """
        logging.info('pattern: %s', pattern)
        results = biglib.query_one(query)
        ic(results)
        return results

    def write_one_result(self, results: List[Dict], cname=None, reset_first=True):
        """write the result of a single funnel"""
        df = pd.DataFrame(results)
        # self.write_gdoc(tabname='simple_funnels_stats', df=df)
        if reset_first:
            self.reset_one_stats(cname=cname)
        biglib.insert_df(df, table_id=self.funnel_stats_table)

    def write_all_results(self, results: List[Dict], reset_first=True):
        df = pd.DataFrame(results)
        # self.write_gdoc(tabname='simple_funnels_rex', df=df)
        if reset_first:
            where = f"chat_set='{self.chat_set}' and funnel_set='{self.set_name}' "
            # where = f"chat_set='{self.chat_set}' "
            biglib.delete(where=where, table_id=self.funnel_stats_table)
        biglib.insert_df(df, table_id=self.funnel_stats_table)

    # def summarize(self):
    #     """aggregate and then cleanup"""
    #     query = f'''
    #         select

    #         from `{self.chat_logs_table}`
    #         where set_name = '{self.set_name}'

    #         group by session
    #         # order by session
    #         # order by max(turn) desc
    #         '''
    #     data = biglib.query_list(query)
    #     logging.info('length of stats %s', len(data))
    #     data = ChatStat.add_exit_items(data)
    #     data = ChatStat.clean_paths(data)
    #     ic('first', data[0])
    #     df = pd.DataFrame(data)
    #     self.df = df
    #     self.write_bq(df=df)
