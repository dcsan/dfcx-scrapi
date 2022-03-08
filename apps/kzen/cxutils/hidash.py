'''various utility funcs inspired by _ / lodash'''


def unpack(turn, fields=None):
    '''a bit specific.. '''
    # TODO generalize
    param=turn['param']
    value=turn['value']
    return param, value

