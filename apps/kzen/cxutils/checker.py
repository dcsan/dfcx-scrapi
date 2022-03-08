'''runtime checks for obvious errors'''

import logging

class ArgError(Exception):
    '''custom exceptions'''

    def __init__(self, message):
        '''simple error'''
        super().__init__(message)
        logging.error('ArgError: %s', message)


def exists(item, msg):
    '''check an arg exists'''
    if not item:
        raise ArgError(msg)


def check_keys(expect, actual, sent, _strict=True):
    """
    compare keys that exist in the expect
    ie do NOT exact compare all fields of the object
    does not recurse currently
    """
    passed = True
    fails = []

    for k in expect.keys():
        v_expect = expect[k]
        try:
            v_actual = actual[k]
        except KeyError as _err:
            logging.debug('err on key: %s', k)
            v_actual = None

    # TODO - recursive compare for nested dict items
    # if isinstance(expect, dict):
    #   return deep_compare(v_expect, v_actual)

        # if not strict:
        #     if isinstance(v_actual, str):
        #         v_actual = texter.normalize(v_actual)
        #     if isinstance(v_expect, str):
        #         v_expect = texter.normalize(v_expect)
        text = sent.get('text')
        if v_actual != v_expect:
            passed = False
            fails.append(
                {
                    'sent.text': text,
                    'key': k,
                    'expect': v_expect,
                    'actual': v_actual,
                }
            )
            # inspect(actual, 'actual')
            # inspect(expect, 'expect')

    return passed, fails
