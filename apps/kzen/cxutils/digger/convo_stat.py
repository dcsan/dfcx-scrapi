"""
outdated - see chat_stat

Summarize conversations based on chatlogs groups

        set_name | sprint
        first_flow | last_flow = main flow outside start flow
        flows = list of flows if more than one
        pages | intents = list of
        driver
        is_xp
        xp_name
        first_driver | last_driver = detected drivers
        escalated = asked for operator?
        instant_operator = operator within 3 calls
        thanks = bot said thanks = tc true?
        tc_guess = automatic stat for task completion = !escalated
        tc_label = manual label for escalated
        target_label = labelled 'goal' for the user even if not reached
        nomatch = was there a no match anywhere?
        start_time | end_time = timestamps
        duration = start-end of whole call

"""

# import logging
# from typing import Dict, List
# import pandas as pd

# from cxutils import biglib
# from cxutils.format.formatter import dumps
# from cxutils.digger.chat_log import ChatLog
# from cxutils.digger.dig_item import DigItem
# from cxutils.digger.chat_static import ChatStatic


# class ConvoStat(DigItem):
#     """for analyzing calls"""

#     def __init__(self, set_name):
#         """create new log"""
#         super().__init__(set_name)
#         self.table_id = biglib.make_table_id('convo_stats')
#         self.chat_logs: ChatLog = None  # other object

#     def load_logs(self):
#         """load original logs to summarize"""
#         self.chat_logs = ChatLog(self.set_name)
#         self.chat_logs.fetch_bq()
#         logging.info('fetched chatlogs %s', len(self.chat_logs.df))

#     def calc_from_logs(self):
#         """calculate paths"""
#         # self.load_logs()
#         # pages = self.chat_logs.df.page.unique()
#         sessions = self.chat_logs.df.groupby(['session'])
#         updated: List[Dict] = []
#         for _index, session in sessions:
#             session['flow'] = 'BILL'
#             driver = session['intent'].map(ChatStatic.first_driver)
#             logging.info('driver %s', driver)
#             session['driver'] = driver.pop()
#             # session['escalated'] = self.check_operator(session)
#             # session['no_match'] = self.check_no_match(session)
#             # session['tc'] = self.guess_tc(session)
#             updated.append(session)

#         df = pd.DataFrame(updated)
#         logging.info('stats \n%s', dumps(updated))
#         # logging.info('stats \n %s', dumps(df[['driver']]))
#         self.debug_df(df)
#         self.write_bq(updated)

#     def process(self):
#         """calculate driver etc"""
#         lines = self.chat_logs.df
#         lines['driver'] = None
#         convos = lines.groupby('session')
#         lines, convos = self.calc_driver(lines, convos)
#         return lines, convos

#     def calc_driver(self, lines, convos):
#         """calc last driving intent based on curated list
#         fill that value to every line of the conversation
#         """
#         for _session_id, convo in convos:
#             driver = ChatStatic.find_first(convo)
#             convo['driver'] = driver
#             lines.loc[lines['session'] == _session_id, 'driver'] = driver
#         return lines, convos

#     def calc_operator(self, lines, convos):
#         """did convo end on an 'operator' """
#         for _session_id, convo in convos:
#             driver = ChatStatic.find_first(convo)
#             lines.loc[lines['session'] == _session_id, 'driver'] = driver
