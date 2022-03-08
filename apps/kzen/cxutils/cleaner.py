'''various utils to clean text'''

import logging


def fix_types(turn):
    '''gspread/sheets doesn't parse booleans well
    so we need to coerce types
    '''
    for k, val in turn.items():
        turn[k] = fix_one(val)

    # fix KEY with space around
    turn = {k.strip(): val for k, val in turn.items()}

    before = turn['value']
    if before in ['false', 'FALSE']:
        turn['value'] = False
    elif before in ['true', 'TRUE']:
        turn['value'] = True
    return turn


def fix_one(val):
    '''just fix strings as results also have spaces'''
    if isinstance(val, str):
        val = val.strip()
        if val in ['false', 'FALSE']:
            return False
        elif val in ['true', 'TRUE']:
            return True
    return val


def parse_int(text):
    '''safe parse to int - stdlib basic stuff'''
    if not text:
        return 0
    try:
        val = int(text)
        return val
    except ValueError:
        logging.warning('cannot parse to int %s', text)
        return 0
