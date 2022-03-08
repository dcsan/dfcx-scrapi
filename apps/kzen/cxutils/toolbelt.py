import logging
from cxutils.format.formatter import dumps


def find_one(items, key, value):
    # next will stop on the first found?
    found = next(f for f in items if f[key] == value)
    if not found:
        logging.warning('find_in not found %s==%s', key, value)
        return None
    return found
