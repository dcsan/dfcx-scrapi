from os import read
from config.base_config import BaseConfig
import logging
from tools.digby.diggable import Diggable
import pandas as pd
# from lib.data.biglib import BigLib
import typing
from tools.digby.diggable import Diggable


class ChatLine(Diggable):

    table_name = 'chat_lines'
    where: str

    def __init__(self, config: BaseConfig, df: pd.DataFrame = None, where=''):
        self.where = where
        super().__init__(df=df, config=config, where=where, table_name=self.table_name)

    def pipeline(self, df=None):
        if df is not None:
            self.df = df
        else:
            self.df = self.read_bq()
        # self.rename_columns()
        self.shifting()
        self.reorder_columns()
        self.write_bq()  # have to write to BQ as convo_log only reads from BQ
        return self.df

    def shifting(self):
        """shift up or down the flows/pages/intents to align next result
        do this with groups so we don't move stuff across a session_id
        """
        df = self.df
        df['page_source'] = df['page']
        df['flow_source'] = df['flow']

        df['agent'] = df.groupby('session_id')['content'].shift(-1)
        df['flow_target'] = df.groupby('session_id')['flow'].shift(-1)
        df['intent_target'] = df.groupby('session_id')['intent'].shift(-1)
        df['match_target'] = df.groupby('session_id')['match_type'].shift(-1)

        # df['triggered_intent'] = df['intent'].shift(-1)
        # df['page_target'] = df['page'].shift(-1)
        # df['flow_target'] = df['flow'].shift(-1)
        # df['match_type'] = df['match_type'].shift(-1)
        self.df = df

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
