"""
    text utilities
"""
import logging
import json
import pprint
pper = pprint.PrettyPrinter(indent=4)


def dumps(obj):
    """try to pretty print a dict/json"""
    try:
        blob = json.dumps(obj, indent=2)
        return blob
    except ValueError:
        # logging.warning('dumps: ValueError')
        return obj
    except TypeError:
        # logging.warning('dumps: TypeError')
        return obj


def pp(obj):
    '''maybe better at serializing to json'''
    return pp(obj)
