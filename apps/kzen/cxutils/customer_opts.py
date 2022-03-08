
"""customer specific settings info"""


def is_head_intent(name):
    '''based on naming convention decide if its a HIT or not'''
    if not name:
        return False
    flag = name.startswith('head_intent') or name.startswith('v2_')
    if flag:
        return True
    else:
        return False
