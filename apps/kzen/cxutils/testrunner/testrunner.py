"""
running a YAML testcase
"""

import logging
import time

import pandas as pd
# import yaml
# from ansimarkup import ansiprint
# from profilehooks import profile

# from cxutils import texter
from cxutils import logit
from cxutils.sheeter import Sheeter
from cxutils import gbot
from cxutils import cleaner

from config import base_config

from .test_dsl import TestDsl

DEFAULT_OPTIONS = {
    'notify': False,
    # 'creds_path': 'creds/default-creds.json'
}

TEST_LIMIT = False
TEST_SHEET_KEY = 'test_runs'  # id for Sheeter of the gdoc containing tests
# magic cell to watch to trigger a run (should be a button/event later)
RUN_CONTROL_CELL = 'B2'


# TODO - check against list of attrs in DSL for valid CMDs

CMDLIST = [
    'setagent',
    'setparam',
    'setenv',
    'send',
    'expect',
    'expectpayload',
    'expectparam',
    'restartagent',
    'jsonpayload'
]

SKIP_COMMANDS = [
    'running'
]

TABLIST = base_config.read('TABLIST')


logging.basicConfig(
    format='[dfcx] %(levelname)s:%(message)s', level=logging.DEBUG)

# SHEET_KEY = 'test_runs'


class TestRunner:
    """Loads a test case and agent in a session
        this class loads a DSL instance and dispatches events to the self.dsl
    """

    def __init__(self, options=None):
        """create new TestRunner
        options:
            - notify: True|False - chatroom notify
            - creds_path
            - verbose
            - sheet_key - use a sheet (otherwise uses BigQuery later)
        """
        # FIXME - rename sheet_key to sheet_cname or id throughout
        # validate options are passed
        self.options = options

        self.verbose = self.options.get('verbose') or False
        self.dsl = TestDsl(self)
        self.cache_data = None
        self.gdoc = self.init_sheet(sheet_key=options['sheet_key'])

    def init_sheet(self, sheet_key=None):
        """connect gdoc sheet"""
        if not sheet_key:
            raise ValueError('no sheet_key passed on testrunner.init_sheet')
        # sheet_key = sheet_key or TEST_SHEET_KEY
        self.gdoc = Sheeter(cname=sheet_key)
        return self.gdoc

    # def run_many_tests(self, tablist=None):
    #     '''run tests across a few tabs of a sheet
    #     was for batch testing a whole suite
    #     '''
    #     tablist = tablist or TABLIST
    #     msg = {}
    #     for tabname in tablist:
    #         if not self.check_tab_run(tabname):
    #             msg[tabname] = 'skip'
    #             time.sleep(0.5) # rate limit on sheets API
    #             continue
    #         # else
    #         results = self.run_one_tab(tabname)
    #         msg['tests'] = len(results) # dataframe
    #         msg['report'] = 'run_many_tests done for %s tabs' % len(tablist)
    #     logging.info(msg)
    #     gbot.notify(msg)
    #     return msg

    def run_one_tab(self, tabname, sheet_key=None, cached=False):
        """run tests in one tab
        Args:
            cached - just load test data once for eg bulk metrics runs
        """
        start_time = time.monotonic()

        self.init_sheet(sheet_key)
        if not cached:
            self.set_tab_run(tabname, 'running')
        results = self.run_story(tabname, cached=cached)
        # logging.info('results %s', results.to_json())
        if not cached:
            self.gdoc.write_tab(tabname, results)
            logit.info(f'<BLUE>test done: {tabname}</BLUE>')
            self.set_tab_run(tabname, 'ready')
        # todo - summarize results and store in BQ
        duration = round(time.monotonic() - start_time)

        msg = {
            'tabname': tabname,
            'sheet_key': sheet_key,
            'duration': f'{duration} seconds'
        }

        msg['lines'] = len(results)   # dataframe
        # msg['report'] = 'run_many_tests done for %s tabs' % len(tablist)
        gbot.send_obj(msg)
        return msg

    def check_tab_run(self, tabname):
        """should we run this tab based on trigger cell"""
        tab = self.gdoc.get_tab_id(tabname)
        if not tab:
            return False
        val = tab.acell(RUN_CONTROL_CELL).value
        if val == 'run':
            return True
        # else:
        return False

    def set_tab_run(self, tabname, runstate):
        """update a tab trigger cell to running/ready etc"""
        tab = self.gdoc.get_tab_id(tabname)
        tab.update(RUN_CONTROL_CELL, runstate)

    def run_story(self, storyname, notify=True, cached=False):
        """run a story which can include a few tests"""
        # storypath = f'public/runs/stories/{storyname}.csv'
        # storydata = inout.load_csv(storypath)

        storydata = self.fetch_test(storyname, cached=cached)

        if notify and not cached:
            gbot.notify(f'run test story: `{storyname}`')

        results = []
        if TEST_LIMIT:
            storydata = storydata[0:TEST_LIMIT]

        count = 0
        for turn in storydata:
            if turn['cmd'] == 'end':
                logging.info('end test early')
                turn['actual'] = 'END RUN'
                turn['error'] = 'END'
                results.append(turn)
                break
            results.append(self.run_turn(turn, count))
            count += 1

        logging.info('ran %s test lines', count)
        # logit.obj('full results', results)
        # make a DF

        # print('results.3', results[3])
        cols = results[1].keys()
        # print('cols', cols)
        df = pd.DataFrame(results, columns=cols)
        # print('results df', df.head(3))
        msg = 'testrunner done for `[ %s ]` lines' % len(df)
        logging.info(msg)
        gbot.notify(msg)

        return df

    def fetch_test(self, storyname, cached=False):
        """fetch from sheet and keep in memory since GAE doesnt allow disc writing"""
        if cached:
            # when we're running a test multiple times in a loop
            if self.cache_data:
                return self.cache_data

        # gdoc = Sheeter(sheet_key=SHEET_KEY)
        df = self.gdoc.read_tab(storyname)
        logging.info('fetched tests [%s]', storyname)
        self.cache_data = df.to_dict('records')
        return self.cache_data

    def run_turn(self, turn, count):
        """test a single send/expect volley pair"""
        # logit.obj('volley', volley)
        if not turn:
            return None

        cmd: str = turn['cmd']
        if not cmd:
            # logging.warning('empty cmd in turn: %s', turn)
            return turn
        cmd = cmd.lower().strip()
        if cmd.startswith('//'):
            return turn  # comment
        if cmd in SKIP_COMMANDS:
            return turn
        if not cmd:
            return turn

        if cmd not in CMDLIST:
            gbot.notify(f'unknown command `{turn}`')
            logging.warning(
                'unknown command: [%s] at row: %i', turn['cmd'], count)
            return turn

        turn = cleaner.fix_types(turn)  # coerce types eg TRUE => boolean True
        turn['count'] = count
        func = getattr(self.dsl, cmd, False)
        logit.info('<GREEN><black>row [%s] %s </black></GREEN>  %s => %s' %
                   (count, cmd, turn['param'], turn['value']))
        if func:
            result = func(turn)  # calls DSL function
            if result['status'] == 0:
                logit.obj('<RED>fail</RED>', result)
                logging.info('result %s', result)
                # logging.info('agent.qr \n %s', self.agent.qr)
            return result

        # else
        logit.info(
            '<RED>cannot find cmd [%s] in turn [%s]</RED>' % (cmd, turn))
        logging.error('cannot find cmd [%s] in turn [%s]', cmd, turn)
        turn['status'] = 0
        turn['actual'] = "cmd not found"
        return turn
