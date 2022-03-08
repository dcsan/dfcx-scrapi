'''
for default configs place in this file
this is the base config so do NOT require anything from here
to avoid circular dependencies
'''

import json
import logging


with open('./config/app_config.json') as f:
    default_config = json.load(f)
    # logging.info('default_config= %s', default_config)


def read(key: str):
    '''read key from JSON file'''
    key = key.upper()
    val = default_config.get(key)
    if not val:
        logging.error('cannot read config val %s', key)
        raise KeyError(f'base_config key not found: {key}')
    return val
