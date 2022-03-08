
# class ConvoLog:
#     '''analyze a convo based on chatlogs'''

#     @staticmethod
#     def make_path(items):
#         '''concat a list of items but remove blanks'''
#         if not items or len(items) is 0:
#             return ''

#         safe = [str(item) for item in items]
#         return ' >> '.join(safe)

#     def calc_paths(self, write_doc=True):
#         '''calculate paths'''
#         df = self.df
#         convo_groups = df.groupby('convo')
#         convos = []
#         for key, convo in convo_groups:
#             #
#             path = convo['intent'].values.tolist()
#             utts = convo['utterance'].values.tolist()
#             turns = len(path)
#             experiment = convo['xp'].iloc[0]
#             convo = {
#                 'is_xp': convo['is_xp'].iloc[0],
#                 'escalated': convo['escalated'].iloc[0],
#                 'convo': key,
#                 'xp': experiment,
#                 'turns': turns,
#                 'path': ChatLog.make_path(path),
#                 'utts': ChatLog.make_path(utts),
#             }
#             # log the first 5 steps in detail
#             # have to pad all values with None or gspread will crash
#             for num in range(5):
#                 if num >= turns:
#                     val = None
#                     utt = None
#                 else:
#                     val = path[num]
#                     utt = utts[num]
#                 convo[f't{num}'] = val
#                 convo[f'utt{num}'] = utt
#             # print('convo', convo)
#             convos.append(convo)

#         logging.info('convos len: %s', len(convos))
#         convos_df = pd.DataFrame(convos)
#         logging.info('convos_df \n%s', convos_df.head(20))
#         if write_doc:
#             self.write_convos(convos_df)

#     def write_convos(self, convos):
#         '''write convos summary to same sheet in 'convos' tab'''
#         tabname = 'convos'
#         self.doc.write_tab(tabname, convos)
#         # TODO write to xp_paths
