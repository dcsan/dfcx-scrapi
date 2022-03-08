'''working with experiments'''

import logging

from dfcx_scrapi.core.conversation import DialogflowConversation

from cxutils.sheeter import Sheeter
from cxutils import biglib
from config import configlib
from config import base_config


class Experimenter:
    '''managing data from experiments'''

    def __init__(self, set_name):
        self.cfg = {
            'set_name': set_name,
            'agent_cname': 'xp-wkshp-v01'
        }
        self.last_reply = {}
        self.table_id = biglib.make_table_id('xp_convos')
        self.set_name = set_name
        self.agent = None
        self.setagent()
        self.gdoc = None

    def setagent(self):
        '''load an agent based on name and existing config in run_configs
        agent is used for detecting intents in no-match lines
        '''
        agent_cname = self.cfg['agent_cname']
        agent = configlib.get_agent(agent_cname)
        agent = dict(agent)
        self.cfg['agent'] = agent
        self.cfg['agent_path'] = agent['agent_path']
        self.creds_path = agent.get(
            'creds_path') or base_config.read('DEFAULT_CREDS_PATH')

        # FIXME use agent_name but have to update schema_ too
        agent_name = agent.get('agent_name')
        # agent_url = agent['agent_url']
        logging.info('agent config %s', agent)
        logging.info('agent_name %s', agent_name)
        logging.info('creds_path %s', self.creds_path)

        # if config['notify']:
        #     logging.info('new test runner %s', config['agent_name'])
        #     gbot.notify(f'testing agent <{agent_url}|{agent_name}>')
        self.agent = DialogflowConversation(
            self.cfg, creds_path=self.creds_path)

    @staticmethod
    def clean_session(df):
        '''remove extra fat from columns'''
        junk = "projects/CUSTOMER-it-pr-pp4v-ppv4-0/locations/global/agents/xxx/environments/yyyy/sessions/"
        df['convo'] = df['session'].map(lambda x: x.lstrip(junk))
        return df

    @staticmethod
    def joinup(items):
        '''concat a list together'''
        # print('items', items)
        if not items or len(items) == 0:
            return ''

        safe = [str(item) for item in items]
        # cat = f'{item} >' for item in items
        return ' > '.join(safe)
        # return ' > '.join(items)

    def load_sheet(self, doc_cname, tabname, delete_first=False):
        '''load gdoc sheet into BQ'''
        self.gdoc = Sheeter(cname=doc_cname)
        df = self.gdoc.read_tab(tabname)
        # df.set_index('num')
        print('before', df.shape)
        print('uniq', df.index.is_unique)

        columns = [
            'session',
            # 'request_timestamp',
            'current_page',
            'user_request',
            'intent_display_name',
            'agent_response',
            'tc',
            'xp',
            'use_case',
            'tc_value',
            'num',
        ]

        df = df.reset_index(drop=True)
        print('step 2\n', df.shape)
        print('step 2\n', df.head(3))
        print('index.uniq', df.index.is_unique)
        print('cols.uniq', df.columns.is_unique)
        print('cols', df.columns)
        print('index', df.index)

        df = df.filter(items=columns, axis='columns')

        # strip empty utterances
        df = df[df['user_request'] != '']
        set_name = self.cfg['set_name']
        df['set_name'] = set_name
        # df = df.drop(columns=['request_timestamp'])

        df = Experimenter.clean_session(df)

        print('step 3\n', df.shape)
        print('s3.head\n', df.head(3))
        table_name = 'xp_convos'
        if delete_first:
            self.delete_set()
        biglib.insert_df(df, table_name)
        return self.gdoc

    def delete_set(self):
        where = f'set_name="{self.set_name}" '
        biglib.delete(table_id=self.table_id, where=where)

    def reply(self, row):
        '''get NLU result from CX'''
        sob = {
            'text': row['user_request']
        }
        self.agent.restart()  # each turn
        self.last_reply = self.agent.reply(sob)
        logging.info('reply %s', self.last_reply)
        return self.last_reply

    def fill_intents(self):
        '''fill in intents and flows that were not found from within other flows'''
        df = self.load_convos(limit=10)
        for index, row in df.iterrows():
            # obj = dict(line)
            # if line['intent_display_name'] is None:
            if row['intent_display_name'] is not None:
                row['top_intent'] = row['intent_display_name']
            else:
                reply = self.reply(row)
                row['top_intent'] = reply['intent_name']
                row['confidence'] = reply['confidence']
                row['target_page'] = reply['page_name']
            print(row)

        print('df', df.head(3))
        # TODO - write intent back to BQ

    def load_convos(self, limit=False):
        '''load all conversation data'''
        set_name = self.cfg['set_name']
        df = biglib.get_df(
            where=f'set_name="{set_name}" ', table_name='xp_convos', limit=limit, order='num')
        df = df.drop(columns=['session'])
        return df

    def check_run(self):
        '''find actual intents for set'''
        df = self.load_convos()
        groups = df.groupby('convo')

        for key, group in groups:
            path = group['intent_display_name'].values.tolist()
            utterances = group['user_request'].values.tolist()

            convo = {
                'convo': key,
                'turns': len(utterances),
                'path': Experimenter.joinup(path),
                'utterances': Experimenter.joinup(utterances)
            }
            print('\n --convo\n', convo)

            # for field in group:
            #     print('field', group[field] )
            # print('line:', line)
            # for field in line:
            #     print('>', field)
            # print('num', row['num'])
            # print(dict(group))

        # print(groups.last()[0:5])
        # print(df.head(3))
        # print(df.shape)

    def calc_sims(self):
        '''find similar phrases within a test set'''
