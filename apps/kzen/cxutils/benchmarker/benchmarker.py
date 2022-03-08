'''
run tests utterance:expect against an agent

'''

import logging
import time
import re
import json
# from sys import stdout

import pandas as pd

from config import base_config, configlib
from cxutils import logit
from cxutils import biglib
from cxutils import customer_opts
from cxutils import gbot
from cxutils import cleaner
from models.test_set import TestSet

from dfcx_scrapi.core.conversation import DialogflowConversation


logger = logging

UPDATE_STEP = 10  # update every 1/X of progress
MAX_INTENTS = 1  # how many alternative confidence items


class BenchMarker:
    '''class for running benchmark tests to check intent detection'''

    # test_set: TestSet
    set_name: str
    agent_name: str
    agent: DialogflowConversation
    table_id: str

    run_config = {
        'hit_only': True,
        'sample': False,
    }

    run_columns = (
        'text',
        'expect',
        'actual',
        'expect_base',
        'actual_base',
        'score',
        'rank',
        'agent',
        'pf',
        'run_id',
        'created_at',
        'hit',
        'expect_hit',
        'actual_hit',
        'active',
        'tags'
    )

    def __init__(self, agent_name: str, set_name: str, reload=True):
        '''create instance
        config:
            agent_name - to run BM against
        '''
        # self.config = config
        # FIX schema to agent_name
        self.agent_name = agent_name
        self.agent = self.get_agent(agent_name)
        self.table_id = biglib.make_table_id('runs')
        self.set_name = set_name
        if reload:
            self.test_data = self.reload_test_data()
        else:
            self.test_data = TestSet.read_bq(set_name)

    def get_agent(self, _config):
        '''get an agent client instance for the whole session'''
        agent_info = configlib.get_agent(self.agent_name)
        creds_path = agent_info.get(
            'creds_path') or base_config.read('DEFAULT_CREDS_PATH')
        agent = DialogflowConversation(
            creds_path=creds_path,
            agent_path=agent_info['agent_path']
        )
        self.agent = agent
        return agent

    def reload_test_data(self):
        '''fetch again from source gdoc'''
        test_set = TestSet(set_name=self.set_name)
        test_data = test_set.fetch_from_gdoc(cname=self.set_name)
        return test_data

    def pass_fail(self, expect, actual):
        '''return integer not boolean,
        so we can do avg() type math on results'''
        if expect == actual:
            return True
        if expect == 'no-match' and actual in [None, 'no-match']:
            logging.info('positive no match')
            return True
        return False

    def remap_intent(self, intent):
        ''' regex mapping of actual intent names
            when trying to compare agents that have different intent names
            trying to widen the catch without catching other intents
            this is since many intents in test sets
            omit the full name of the intent
            NOTE: this currently rips out 'head_intent'
        '''

        base = intent
        if not base:
            # logging.warning('no base passed to remap intent')
            return None

        strip_list = [
            'device_protect',
            'suspend_reconnect',
            'live_chat',
            'merged',
            'plan_add_change',
            'explain_bill',
            'order',
            'troubleshoot',
            'maintenance']
        for item in strip_list:
            if item in base:
                pattern = '^{}.'.format(item)
                temp_str = re.sub(pattern, '', base)
                base = temp_str
        # plan_add_change.head_intent.plan_change =>
        # head_intent.plan_change
        check = re.match(".*(head_intent.*)", intent)
        if check and check.groups():
            base = check.groups()[0]

        # just strip head_intent
        base = re.sub(r'^head_intent\.', '', base)

        # logger.info('intent: \n %s => \n %s', intent, base)

        return base

    def check_intent(self, row, max_intents=1) -> pd.DataFrame:
        '''check all intents for a match for lower confidence checks
        max_intents: how many intents to log. 1= just the first matched intent
        '''

        text = row.text
        if not text:
            logging.error('row has no .text %s', row)
            gbot.fatal('no text in row')

        send = {
            'text': text
        }
        reply = self.agent.reply(send, restart=True)
        intent = reply.get('intent_name')
        df = pd.DataFrame({}, columns=BenchMarker.run_columns)

        expect = None
        try:
            expect = row.expect
        except AttributeError as err:
            logging.error('row has no expect\n%s', row)
            logging.error('text: %s', text)
            gbot.fatal('row has no expect', row)
            return df
            # raise(err)

        expect_base = self.remap_intent(expect)

        if not reply or not intent:
            """usually this only happens in error condition or
            complete no match or default fallback intent"""
            logger.warning('no reply for text: %s', text)
            logger.warning('reply %s', reply)

            actual = 'no-match'
            pf = self.pass_fail(expect, actual)

            score = 0
            if expect == 'no-match':
                # expected a no-match
                score = 1

            result = {
                'expect': expect,
                'expect_base': expect_base,
                'actual': 'no-match',
                'actual_base': 'no-match',
                'text': text,
                'active': True,
                'set_name': row.set_name,
                'pf': pf,
                'score': score,
                'hit': 0,
                'rank': 0,
                'no_match': 1
            }
            logging.info('empty result %s', result)
            df = df.append(result, ignore_index=True)
            return df

        # for item in intents[:max_intents]:
        item = {}

        item['text'] = text
        item['expect'] = expect
        item['expect_base'] = expect_base
        item['active'] = True
        item['set_name'] = row.set_name
        item['no_match'] = 0
        item['hit'] = int(customer_opts.is_head_intent(row.expect))
        item['expect_hit'] = customer_opts.is_head_intent(row.expect)
        item['actual_hit'] = customer_opts.is_head_intent(item.get('name'))
        item['score'] = reply.get('confidence')

        # item['weight'] = ...
        # item['weighted_passrate']

        actual = intent  # item.get('name', None)
        item['actual'] = actual
        if actual:
            actual_base = self.remap_intent(actual)
            item['actual_base'] = actual_base
            item['pf'] = self.pass_fail(expect_base, actual_base)
        # else:
        #     """could be null"""
        #     item['actual'] = None
        #     if item['expect'] == 'NONE' or item['expect'] == 'null':
        #         item['pf'] = True  # no match was expected
        #     else:
        #         item['pf'] = False
        if item.get('name'):
            del item['name']

        # TODO - set false_neg / false_pos / pass_rate / distance
        # logger.info('item:\n %s', item)
        # print('item:', item)
        df = df.append(item, ignore_index=True)

        return df

    # def load_test_set(self, sample=False):
    #     '''Load test data set from CSV
    #         looks first in the config, then BM.config

    #         args:
    #             sample: int|False - just use a random sample to test with
    #     '''
    #     config = self.config
    #     fp = config.get('test_set') or BenchMarker.run_config.get('test_set')
    #     test_set = pd.read_csv(fp, header=0)

    #     # add hit flag column based on intent_ name
    #     test_set['hit'] = test_set['expect'].apply(cust_opts.is_head_intent)
    #     # hit_only = one_config.get('hit_only', True)
    #     logit.head(test_set, limit=3)
    #     logger.info('full test_set len %i', len(test_set))

    #     # assume miniset is ALL HITs
    #     # if hit_only:
    #     #     # filter cannot take 'is'
    #     #     test_set = test_set[test_set['hit'] == True]
    #     #     logger.info('hit only test_set len %s', len(test_set))

    #     sample = config.get('sample', False) or sample
    #     if sample:
    #         sample = min(sample, len(test_set))
    #         test_set = test_set.sample(sample)

    #     logger.info(
    #         '--- load_test_set [%s] sample: [%i] len: [%i]',
    #         fp,
    #         sample,
    #         len(test_set))

    #     return test_set

    # def init_results_file(self):
    #     '''create a blank CSV file with the right column names'''
    #     blank = pd.DataFrame({}, columns=BenchMarker.run_columns)
    #     blank.to_csv('public/runs/results/intent-runs.csv', index=False)

    # def test_reply(self):
    #     '''test a single reply'''
    #     one_config = configlib.get_configs(defaults=run_config)[1]
    #     agent = self.get_agent(one_config)
    #     send = {
    #         'text': 'change an e_mail'
    #     }
    #     reply = agent.reply(send)
    #     print(reply)

    def summarize(self, df):
        summary = {
            'mean': df['score'].mean()
        }
        return summary

    def run_one_set(self, sample=False, max_intents=1):
        '''run one full set against an agent'''
        # config = self.config
        start = time.time()
        agent_name = self.agent_name
        results = pd.DataFrame(columns=BenchMarker.run_columns)

        set_name = self.set_name

        steps = 200  # notify every 200
        count = 0

        test_df = self.test_data

        sample = cleaner.parse_int(sample)
        if sample:
            test_df = test_df[:sample]
        total = len(test_df)

        msg = f'--------------------------------\n 🟩 START BenchMark* \nagent: `{self.agent_name}` \nset_name `{set_name}` '
        gbot.notify(msg)
        gbot.notify(
            f'test_df len: `{len(test_df)}` \n ```{test_df.head(3)}``` ')

        # can have many rows
        one_result = pd.DataFrame()  # empty

        for row in test_df.itertuples():
            count += 1
            if sample and count > sample:
                break

            one_result = self.check_intent(row, max_intents=max_intents)

            if count % steps == 0:
                pct = int(count * 100 / total)
                msg = (
                    f'`[{pct}%]` {set_name} x {self.agent_name} | at {count}/{total} ')
                gbot.notify(msg)
                logging.info('check [%s]: \n %s => %s', count,
                             one_result.iloc[0].text, one_result.iloc[0].actual)
            results = results.append(one_result)

        # set some DF level properties
        results['agent'] = agent_name
        # result['tags'] = config.get('tags')

        logger.info('writing BM.run result: %s', agent_name)
        # fp = f'public/runs/results/intent-runs.csv'
        # with open(fp, 'a') as fd:
        #     result.to_csv(fd, header=False, index=True)
        #     result.to_csv(fp, index=False)

        logger.info('got result length: %i', len(results))
        results['run_id'] = int(time.time())
        results['created_at'] = int(time.time())

        # biglib.remove_run(agent=agent_name)
        where = f' agent="{self.agent_name}" and set_name="{set_name}" '''
        biglib.delete(table_id=self.table_id, where=where)
        biglib.insert_df(results, table_name='runs')
        # biglib.save_run(results)
        endtime = time.time()
        duration = int((endtime - start) / 60)
        summary = self.summarize(results)

        msg = f'done \nagent: `{self.agent_name}` \nduration `{duration}` mins \nset_name: `{set_name}`\nrows: `{len(one_result.index)} ` \n\nsummary: '
        msg += json.dumps(summary)
        msg += '\n✅ *DONE BenchMark!*\n-------------------------------'
        gbot.notify(msg)

        output = {
            'df': results,
            'summary': summary
        }
        return output
