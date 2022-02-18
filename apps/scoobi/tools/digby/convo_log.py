import logging
import pandas as pd
from typing import Any
from lib.data.biglib import BigLib

from tools.digby.diggable import Diggable
from lib.util.text_util import TextUtil


class ConvoLog(Diggable):
    # read from here
    source_table_name = 'chat_logs'
    source_table_id: str

    # write to here
    table_name = 'convo_logs'

    def __init__(self, config, df=None, where=''):
        super().__init__(df=df, config=config, where=where, table_name=self.table_name)
        self.source_table_id = BigLib.make_table_id(self.source_table_name)

    def group_convos_from_logs(self):
        '''read the data from source_table/chat_logs table
        and group into sessions
        and calculate paths
        '''

        qs = f"""
            SELECT

            session_id,

            string_agg(
                flow, '\\n'
                order by position asc
            ) as flows,

            string_agg(
                page, '\\n'
                order by position asc
            ) as pages,

            string_agg(
                role, '\\n'
                order by position asc
            ) as roles,

            string_agg(
                intent, '\\n'
                order by position asc
            ) as intents,

            string_agg(
                reason, '\\n'
                order by position asc
            ) as reasons,

            string_agg(
                cast(position as string), '\\n'
                order by position asc
            ) as positions,

            string_agg(
                content, '\\n'
                order by position asc
            ) as contents,

            max(abandoned) as abandoned,
            max(contained) as contained,
            max(handoff) as handoff,
            max(escalated) as escalated,
            max(tc_check) as tc_check,
            max(operator_check) as operator_check,
            max(escalated_check) as escalated_check,
            max(abandoned_check) as abandoned_check,
            max(intent_detail) as intent_detail,
            sum(no_input_check) as no_input_total,
            sum(no_match_check) as no_match_total,
            max(tc) as tc,
            max(exit) as exit,
            max(use_case) as use_case,

            # will max work on strings?
            max(position) as total_positions,
            max(current_sprint_number) as current_sprint_number,
            max(channel) as channel,

            FROM `{self.source_table_id}`

            # where clause:
            {self.where}

            group by session_id
            order by session_id

        """

        self.df = BigLib.query_df(qs)
        if len(self.df) < 1:
            logging.warning('no result for convo logs where=%s', self.where)

        return self.df
        # self.truncate()
        # self.write_bq(df)

    def dedupe_paths(self, df=None) -> pd.DataFrame:
        df = df if df is not None else self.df
        path_list = []
        logging.info('path items %s', len(df))
        for (index, row) in df.iterrows():
            if (index % 100 == 0):
                logging.info('row %s', index)
            pages = TextUtil.split_items(row, 'pages')
            reasons = TextUtil.split_items(row, 'reasons')
            # logging.info('row %s => \n%s', index, row)
            path = ""
            for idx, page in enumerate(pages):
                try:
                    path += f'{pages[idx]} >> {reasons[idx]}\n'
                except IndexError as err:
                    # FIXME probably reasons is missing ending point
                    # maybe related to last line of convo?
                    logging.error(
                        'items length mismatch \n pages:   %s \n reasons: %s', pages, reasons)
                    path += f'{pages[idx]} >> x'
            # path = [f'{page} >> {reason}'
            #         for page in pages
            #         for reason in reasons]
            # print('path', path)
            row['path'] = path
            path_list.append(row)
        paths_df = pd.DataFrame(path_list)
        paths_df.drop_duplicates(inplace=True)  # type: ignore
        return paths_df

    def pipeline(self):
        self.df = self.group_convos_from_logs()
        self.reorder_columns()
        self.df['pages_dd'] = self.df.apply(self.pages_dd, axis=1)
        self.write_bq()
        return self.df

    def pages_dd(self, row):
        '''remove duplicated pages for each convo'''
        pages = row.get('pages')
        if pages:
            pages = pages.split('\n')  # FIXME later do in a stats table?
            pages_dd = TextUtil.remove_seq_dupes(pages)
            return '\n'.join(pages_dd)  # to fit in one cell
        return None
