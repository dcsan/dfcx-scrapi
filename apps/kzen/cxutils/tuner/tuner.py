"""Tuner for intents"""

# import json
# import en_use_md
import logging

import pandas as pd
from fuzzywuzzy import fuzz

# from cxutils import logit
from cxutils import biglib
from cxutils import gbot
from cxutils.format.formatter import dumps

from models.test_set import TestSet

# import spacy_universal_sentence_encoder

FORMAT = '%(message)s'
logging.basicConfig(format=FORMAT)

SIM_THRESHOLD = 0.4  # min similarity threshold
NOTIFY_INTERVAL = 1000  # every 1000 send a notify

MODEL_PATHS = {
    'lg': './data/models/en_core_web_lg-3.0.0/en_core_web_lg/en_core_web_lg-3.0.0',
    'md': './data/models/en_core_web_md-3.0.0/en_core_web_md/en_core_web_md-3.0.0',
    'sm': './data/models/en_core_web_sm-3.0.0/en_core_web_sm/en_core_web_sm-3.0.0',
}


class Tuner:
    """tune intents"""

    def __init__(self, set_name, agent_name=None):
        """create a new model to manage intent tuning"""

        self.agent_name = agent_name  # not used atm
        self.set_name = set_name
        self.test_set = TestSet(set_name)
        self.set_data = None
        self.intents = []
        self.nlp = None
        self.model_type = 'md'

    def init_nlp(self, model_type='md', reload=False):
        """defer loading spacy and tensor flow until we have to"""
        import spacy

        if not self.nlp or self.model_type != model_type:
            logging.info(
                'load spacy model: [%s]', model_type)
            if model_type == 'use':
                # self.nlp = en_use_md.load()
                # self.nlp = spacy.load('en_core_web_sm')
                # import spacy
                # self.nlp = spacy.load('en_use_md')
                # self.nlp.add_pipe('universal_sentence_encoder')
                self.model_type = model_type
                self.nlp = spacy.load('en_use_md')

            elif model_type in MODEL_PATHS:
                self.model_type = model_type
                self.model_path = MODEL_PATHS[self.model_type]
                self.nlp = spacy.load(self.model_path)
            logging.info('DONE load spacy model')

    def load_intents(self):
        """load stuff"""

        intent_list = self.test_set.load_intents()

        # intent_list = intents['intent'].tolist()
        # avoid empty keys
        intent_list = sorted(intent_list, key=lambda x: x['intent'] or "")
        logging.info('intents for set [%s] len: %s',
                     self.set_name, len(intent_list))

        obj = {
            'agent_name': self.agent_name,
            'set_name': self.set_name,
            'item_list': intent_list
        }
        logging.info('tuner %s', obj)
        return obj

    def load_phrases(self, intent=None):
        """load training phrases
        args:
            intent: name of intent. if None will get all phrases in set
        """
        phrase_list = self.test_set.load_phrases(intent_name=intent, limit=0)
        # phrase_list = sorted(phrases, key=lambda x: x['utterance'] or "" ) # avoid empty keys
        # logging.info('phrase_list\n %s', phrase_list )
        obj = {
            'agent_name': self.agent_name,
            'set_name': self.set_name,
            'item_list': phrase_list
        }
        logging.info(
            'phrases for intent [%s] = len: [%s]', intent, len(phrase_list))
        return obj

    def calc_one(self, item1, item2, field_name, threshold):
        threshold = threshold or SIM_THRESHOLD
        """simple similarity comparison"""
        # -> Optional[dict[str, Any]]:
        text1 = item1[field_name]
        text2 = item2[field_name]
        lev = self.calc_lev(text1, text2)
        vec = self.calc_spacy(text1, text2)
        avg = (lev + vec) / 2
        valid = True if vec > threshold else False
        sim = {
            'valid': valid,
            'lev': lev,
            'avg': avg,
            'vec': vec  # last word vector calc
        }
        sim[self.model_type] = vec  # for each calc type in case we re-run
        return sim
        # logging.info('sim %s', dumps(sim))

    def calc_spacy(self, text1, text2):
        """calc similarity with spacy model"""
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        return doc1.similarity(doc2)

    def calc_lev(self, text1, text2):
        """calc levenshtein distance as 0-1 range float"""
        ratio = fuzz.ratio(text1, text2) / 100.0
        return ratio
        # ratio_sort = fuzz.token_sort_ratio(text1, text2)
        # ratio_part = fuzz.partial_ratio(text1, text2)
        #
        # if ratio > threshold:
        #     return ratio
        #     # logging.info('ratio %s \n%s | \n%s', ratio, item1, item2)
        # return  0

    def scan(self, intent=None, threshold=None, hide_same_intent=True, model_type='md'):
        """calculate similarities
        args:
            hide_same_intent: dont show similar phrases in the same intent
        """
        # intents = self.load_intents()['item_list']
        # intent_names = [item['intent'] for item in intents]
        # self.count_sims()
        # return
        self.init_nlp(model_type, reload=True)
        threshold = threshold or SIM_THRESHOLD
        logging.info('scan threshold=%s', threshold)
        sims = []
        field_name = 'utterance'
        phrases = self.load_phrases(intent=intent)['item_list']
        count = 0
        total = len(phrases) ** 2
        gbot.notify(
            f'''-------\nstart scan
                set_name: `{self.set_name}`
                threshold: `{threshold}`
                model_type: `{model_type}`
                total: `{total}`
            ''')

        for item1 in phrases:
            for item2 in phrases:
                count += 1
                if count % NOTIFY_INTERVAL == 0:
                    pct = int(100*count/total)
                    gbot.notify(f'{pct}% {count}/{total}')
                if item1['uuid'] == item2['uuid']:
                    continue
                if hide_same_intent and item1['intent'] == item2['intent']:
                    # logging.info('skip %s \t%s\t%s', item1['intent'], item2['intent'])
                    continue
                # logging.info('compare', item1, item2)
                # need to prefix left and right so we dont get sankey loops
                leftIntent = 'L.' + item1['intent']
                rightIntent = 'R.' + item2['intent']
                sim = self.calc_one(
                    item1, item2, field_name, threshold=threshold)
                if sim.get('valid') is not True:
                    continue
                    # logging.info('not valid %s', dumps(sim))
                else:
                    one_sim = {
                        'set_name': self.set_name,
                        'intent1': leftIntent,
                        'intent2': rightIntent,
                        'text1': item1['utterance'],
                        'text2': item2['utterance'],
                        'uuid1': item1['uuid'],
                        'uuid2': item2['uuid'],
                        'diff': sim.get('lev') - sim.get('vec'),
                        # 'lev': sim.get('lev'),
                        # 'vec': sim.get('vec'),
                        # 'avg': sim.get('avg'),
                    }
                    one_sim.update(sim)  # other md,lg,use etc values
                    # logging.info('sim \n%s', dumps(one_sim))
                    sims.append(one_sim)

        df = pd.DataFrame(sims)
        gbot.notify(
            f'done scan `set_name:{self.set_name}`  found sims: {len(sims)}')
        self.calc_sim_stats(df)
        where = f'set_name = "{self.set_name}"'
        biglib.delete(table_name='sims', where=where)
        biglib.insert_df(df, table_name='sims', if_exists='append')
        self.count_sim_phrases()
        return sims

    def calc_sim_stats(self, df=None):
        """calc the similarity across intents for sankey display"""
        if df is None:
            table_id = biglib.make_table_id('sims')
            df = biglib.query_df(
                f'select intent1, intent2, set_name from {table_id} where set_name="{self.set_name}" ')

        # TODO - this just counts the number of sims,
        # we also want an avg of (use/lev) similarity
        sim_stats = df.groupby(['intent1', 'intent2', 'set_name']).size()
        sim_stats = sim_stats.reset_index(name='count')
        where = f'set_name = "{self.set_name}"'
        biglib.delete(table_name='sim_stats', where=where)
        biglib.insert_df(sim_stats, table_name='sim_stats')
        gbot.notify(
            f'added sim_stats for set_name: {self.set_name} len: {len(sim_stats)}')

        # logging.info('sim_stats \n %s', sim_stats)

    def get_sim_stats(self):
        """get sim_stats from DB as list for json response"""
        table_id = biglib.make_table_id('sim_stats')
        query = f'''
            select * from {table_id}
            where set_name="{self.set_name}"
            order by intent1, intent2'''
        sim_stats = biglib.query_list(query)
        return sim_stats

    def get_sankey(self, right=None, threshold=SIM_THRESHOLD):
        """format stats so we can draw a sankey easily"""
        # calc intersection against another set?
        sim_stats = self.get_sim_stats()
        flat_stats = []
        for stat in sim_stats:
            flat_stats.append([
                stat['intent1'],
                stat['intent2'],
                stat['count']
            ])
        return flat_stats

    def get_simset(self, left, name=None, threshold=SIM_THRESHOLD):
        """get a subset of sim values for one intent to present next to sankey"""
        table_id = biglib.make_table_id('sims')
        where = f"\n where intent1='{left}' and set_name='{self.set_name}' "
        query = f"select * from {table_id} {where} order by intent2, text1, vec desc"
        blob = biglib.query_list(query)
        # logging.info('simset \n%s', dumps(blob))
        return blob

    @staticmethod
    def update_phrase(phrase):
        """update single item in bigquery - very slow so not used"""
        table_id = biglib.make_table_id('test_sets')
        qstring = f'''
            update {table_id}
            set sim_count={phrase['sim_count']}
            where uuid = '{phrase['uuid']}'
        '''
        logging.info('sq %s', qstring)
        biglib.query(qstring)

    def count_sim_phrases(self, _intent=None):
        """update all phrases in the test set with count of sims"""
        phrases = self.load_phrases()['item_list']
        sims = Tuner.load_sims(set_name=self.set_name)['item_list']
        gbot.notify(
            f'_START_ *count sims* set_name:`{self.set_name}` phrases:`{len(phrases)}` ')
        for phrase in phrases:
            sim_set = [
                sim for sim in sims
                if sim['uuid1'] == phrase['uuid']
            ]
            # if len(sim_set):
            phrase['sim_count'] = len(sim_set)
            # self.update_phrase(phrase)

        # could maybe do an update here instead but we just delete and create
        # so we can do it in one big dataframe insert
        # FIXME - currently a normal benchmark run with also overwrite this simset data
        df = pd.DataFrame(phrases)

        print(df.head(3).transpose())
        print(df[['uuid', 'sim_count']])

        biglib.delete(table_name='test_sets',
                      where=f'set_name="{self.set_name}" ')
        biglib.insert_df(df, table_name='test_sets')
        gbot.notify(
            f'✔ *DONE* count sims set_name:`{self.set_name}` phrases:`{len(df)}` sims:`{len(sims)}`\n_________ ')

    @classmethod
    def load_sims(cls, uuid=None, set_name=None):
        """for a single phrase based on a uuid"""
        table_id = biglib.make_table_id('sims')
        if uuid:
            where = f'where uuid1="{uuid}" '
        elif set_name:
            where = f'where set_name="{set_name}" '
        else:
            where = ''

        query = f'''
            select * from {table_id}
            {where}
            order by intent2
        '''
        sims = biglib.query_list(query)
        obj = {
            'item_list': sims
        }
        logging.info('sims len %s', len(sims))
        return obj

    def test(self):
        """simple self test"""
        return self.scan()
