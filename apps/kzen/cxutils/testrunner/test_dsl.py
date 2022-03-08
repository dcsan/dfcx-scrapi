'''
DSL for test commands
based on the testrunner for access to agent
'''

from dfcx_scrapi.core.conversation import DialogflowConversation

import json
import re
import logging
from typing import List, Tuple

# import google.api_core.exceptions.NotFound

from config import configlib
from config import base_config

from cxutils import checker
from cxutils import hidash
from cxutils import gbot
from cxutils import cleaner


# DSL commands
# from cx_testrunner.config import configlib


class TestDsl():
    '''test commands invoked from testRunner
    correspond to cmd column in test sheet
    this class creates an instance of the conversation agent
    '''

    def __init__(self, runner):
        self.runner = runner
        self.config = {}
        self.agent = None
        self.env = {}
        self.next_message = {}
        self.last_reply = {}
        self.cx_environment = None
        self.cx_experiment = None
        self.disable_webhook = False  # can be overridden later
        self.creds_path = None

    def log_handler(self, turn, msg, status, log_level='info'):
        """
        error handling
        :param msg:
        :param log_level:
        :param turn:
        :return:
        """
        turn['status'] = status
        if log_level.lower() == 'info':
            logging.info(msg)
        if log_level.lower() == 'debug':
            logging.debug(msg)
        if log_level.lower() == 'error':
            turn['error'] = msg
            logging.error(msg)
        if log_level.lower() == 'warning':
            logging.warning(msg)

        return turn

    def reset_message(self):
        '''clear all params for pending message
        we use this 'next_message' so that params can all be staged on a message
        and sent together
        '''
        self.next_message = {}

    def setagent(self, turn):
        '''load an agent based on name and existing config in run_configs'''
        agent_name = turn['value']
        checker.exists(agent_name, 'no agent_name passed to setagent')
        config = configlib.get_agent(agent_name)
        config = dict(config)
        # logging.info('config %s', config)
        config.update(self.runner.options)  # modify in place
        self.config = config
        self.creds_path = config.get(
            'creds_path') or base_config.read('DEFAULT_CREDS_PATH')

        # FIXME use agent_name but have to update schema_ too
        agent_name = config.get('agent_name')
        agent_url = config['agent_url']
        logging.info('agent config %s', config)
        logging.info('agent_name %s', agent_name)
        logging.info('creds_path %s', self.creds_path)

        # if config['notify']:
        #     logging.info('new test runner %s', config['agent_name'])
        #     gbot.notify(f'testing agent <{agent_url}|{agent_name}>')
        self.agent = DialogflowConversation(config, creds_path=self.creds_path)
        turn['actual'] = agent_url
        turn['status'] = 'ok'
        return turn

    # def running(self, turn):
    #     '''triggered as a command when script setse cell to "running" '''
    #     return turn

    # def run(self, turn):
    #     '''alias for running'''
    #     return turn

    def setenv(self, turn):
        '''set env values for run'''
        param, value = hidash.unpack(turn)
        logging.info('setenv [%s] => %s', param, value)
        self.env[param] = value
        # if param == 'webhooks':
        #     # TODO - call the agent to toggle webhooks
        #     # logging.info('not supported yet - set webhooks: %s', value)
        #     self.disable_webhook = value # should be coerced
        #     turn['status'] = f'set webhook: ${value}'
        # if param in ['environment', 'experiment']:
        # have to pass this onto the agent
        self.agent.set_agent_env(param, value)
        turn['status'] = 'ok'
        return turn

        # else:
        # turn['status'] = 'ok'
        # return turn

    def setparam(self, turn):
        '''set params on next message'''
        param, value = hidash.unpack(turn)
        if isinstance(value, str) and value.startswith('[{'):
            try:
                value = json.loads(value)

            except ValueError as err:
                logging.error('bad json\n %s', err)
                turn['status'] = 'error'
                turn['error'] = 'bad json'
                return turn

        self.next_message['params'] = self.next_message.get('params') or {}
        self.next_message['params'][param] = value
        logging.debug('setParam %s', turn)
        turn['status'] = 'ok'
        return turn

    # def setenvironment(self, turn):
    #     '''set environment to be used for testing'''
    #     _param, value = hidash.unpack(turn)
    #     self.cx_environment = value
    #     logging.debug('setEnvironment %s', turn)
    #     turn['status'] = 'ok'
    #     return turn

    # def setexperiment(self, turn):
    #     '''set test experiment to be used for testing'''
    #     _param, value = hidash.unpack(turn)
    #     self.cx_experiment = value
    #     logging.debug('setExperiment %s', turn)
    #     turn['status'] = 'ok'
    #     return turn

    def send(self, turn):
        '''send message with params'''
        param, value = hidash.unpack(turn)
        # Splits the buttons to send text separately
        # example : "Plan options>>Bill charges>>AT&T TV"

        split_buttons = value.split(">>")
        for routes in split_buttons:
            if param == 'text':
                self.next_message['text'] = routes
            elif param == 'dtmf':
                self.next_message['dtmf'] = routes
            # else:
            #     # no message payload
            #     pass
            reply, error = self.safe_send(turn)
            if error:
                turn['error'] = error
                turn['status'] = 0
                # continue to next line????
            else:
                # FIXME - we only return ONE turn
                # but in fact the above code runs through an array of turns?
                self.last_reply = reply
                logging.debug('reply OK %s', self.last_reply)
                turn['status'] = 'ok'
                self.reset_message()
                # continue to next line???? then turn will get overwritten

        return turn
        # # logit.obj('got reply', self.last_reply)
        # logging.debug('reply %s', self.last_reply)
        # turn['status'] = 'ok'
        # self.reset_message()
        # return turn

    def safe_send(self, turn) -> Tuple[str, bool]:
        """send to SAPI library with wrapper for API exceptions"""
        try:
            reply = self.agent.reply(
                self.next_message,
                # FIXME - are we still implementing this? needs more testing
                # disable_webhook=self.disable_webhook
            )
            return reply, False

        # FIXME - actual google core error have to import somehow
        # except google.api_core.exceptions.NotFound
        except BaseException as err:
            # FIXME add function to handle all error logging as formats are mixed
            logging.error('DFCX API error %s', err)
            count = turn['count']
            gbot.notify(
                f'API err on turn {count} \n```{turn}``` \n```{err}```')
            # FIXME better handling for error results
            return err, True

    def expectparam(self, turn):
        '''check a param value on last reply'''
        # TODO merge with expect
        param, value = hidash.unpack(turn)
        if not self.last_reply:
            gbot.notify(f'no reply turn `{turn}`')
            turn['actual'] = 'NONE'
            turn['error'] = 'API error?'
            turn['ok'] = 0
            return turn

        try:
            actual = self.last_reply['params'][param]
            # if not isinstance(actual, str):
            #     # FIXME - we just convert to a string but maybe upstream can fix this
            #     logging.error('received not string type for param %s', actual)
            #     logging.info('expectparam %s expect: %s = actual: %s', param, value, actual)
            #     logging.info('params %s', self.last_reply['params'])
            #     actual = str(actual)
            turn['actual'] = actual

        except KeyError as err:
            gbot.notify(f'KeyError [{param}] {turn} ')
            logging.error(
                'KeyError failed expect for param [%s] \n`%s`', param, err)
            if turn['value'] and turn['value'] not in [None, 'NULL']:
                turn['status'] = 0
            turn['actual'] = f'key not found {param}'
            turn['comment'] = f'// key not found {param}'
            return turn

        # Converting value to float to match actual
        if param == 'PUG':
            value = float(value)

        if value == actual:
            turn['status'] = 1
        else:
            turn['status'] = 0
        return turn

    def expectpayload(self, turn):
        '''custom payload'''
        param, value = hidash.unpack(turn)
        check = False
        logging.info('payload reply %s', self.last_reply)

        if self.last_reply.get('payload') is not None:
            payload = self.last_reply.get('payload')
        else:
            payload = str(self.last_reply.get('text')).replace('\n', '')
            value = str(value).replace('\n', '')

        if not payload:
            turn['actual'] = 'no payload'
            turn['status'] = 0
            return turn

        # else
        # as a string for sheets to display
        jsonstr = json.dumps(payload, ensure_ascii=False)
        turn['actual'] = jsonstr
        if turn['param'] == 'contains':
            # just search as a string
            if value in jsonstr:
                check = True
        elif turn['param'] == 'equalTo':
            # just search as a string
            if sorted(json.loads(value).items()) == sorted(json.loads(jsonstr).items()):
                check = True
        elif turn['param'] == 'expectedJson' or 'expectedConversation':
            # just search as a string
            if sorted(json.loads(value)['expectedPayload'].items()) == sorted(json.loads(jsonstr).items()):
                check = True
        else:
            if payload[param] == value:
                check = True
        turn['status'] = 1 if check else 0
        turn['error'] = f"The Payload doesnt matches,the actual response is {jsonstr}" if not check else ''
        return turn

    def expect(self, turn):
        '''check last_reply'''
        param, value = hidash.unpack(turn)

        if not self.last_reply:
            gbot.notify(f'no reply turn `{turn}`')
            turn['actual'] = 'NONE'
            turn['error'] = 'API error?'
            turn['ok'] = 0
            return turn

        try:
            if param in ['regex', 'text']:
                actual = self.last_reply['text']
            else:
                actual = self.last_reply[param]
        except KeyError:
            logging.warning('failed expect for param [%s]', param)
            turn['actual'] = 0
            turn['error'] = 'KeyError'
            return turn

        except TypeError as err:
            logging.warning(
                'failed reply usually API error for turn [%s]\n[%s]', turn, err)
            turn['actual'] = 0
            turn['error'] = 'TypeError'
            return turn

        actual = cleaner.fix_one(actual)
        turn['status'] = 0  # default fail
        turn['actual'] = actual
        if param == 'text':
            if actual.startswith(value):
                turn['status'] = 1
                # turn['comment'] = 'text match'

        elif param == 'regex':
            match = re.search(value, actual)
            logging.info('match %s', match)
            if match:
                turn['status'] = 1
            else:
                turn['comment'] = '// regex mismatch'
        else:  # some other param like intent/page etc.
            turn['status'] = int(actual == value)  # want a numeric value

        # logit.obj('expect:', turn)
        # logit.obj('actual:', actual)
        return turn

    def restartagent(self, turn):
        '''start a new session on the agent'''
        self.agent.restart()
        # self.agent = DialogflowConversation(self.config)
        turn['status'] = 'ok'
        # turn['comment'] = '// tr created new agent'
        # time.sleep(5)
        return turn

    def jsonpayload(self, turn):
        """send message with json"""
        param, value = hidash.unpack(turn)
        try:
            if param == 'text':
                self.next_message['text'] = json.loads(value)['text']
                self.last_reply = self.agent.reply(self.next_message)
                self.setparam(turn)
            elif param == 'chat':
                utterances = json.loads(value)['text'].split('>')
                for each_utter in utterances:
                    self.next_message['text'] = each_utter
                    self.last_reply = self.agent.reply(self.next_message)
                    self.setparam(turn)

            self.log_handler(
                turn, f'reply %s, {self.last_reply}', 'ok', 'debug')
            if json.loads(value)['intent_name'] == self.last_reply['intent_name']:
                turn = self.expectpayload(turn)
                if turn['status'] == 0:
                    self.log_handler(
                        turn, f'The response is incorrect', 0, 'error')
            else:
                self.log_handler(
                    turn, f'The intent name is incorrect', 0, 'error')
            self.reset_message()
            return turn

        except ValueError as err:
            self.log_handler(turn, f'Bad json %s, {err}', 0, 'error')
