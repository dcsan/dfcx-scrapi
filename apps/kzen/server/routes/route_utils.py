"""utils to help with routing"""
import logging
from flask import Flask, render_template, request  # escape

from cxutils.format import coerce
from cxutils.format.formatter import dumps


APP_TOKEN = 'runfoo!'
# APP_TOKEN = "95959660-a245-4ac7-b05c-fcb491e3fa40"
# APP_TOKEN = uuid.uuid4()
logging.info('using token: %s', APP_TOKEN)


def logit(msg, obj=None):
    """so we can see logs locally and in logging console"""
    print(msg, obj)
    logging.info('%s: %s', msg, obj)


def check_token():
    """check our api token"""
    user_token = request.args.get('token')
    logging.info('main.start')
    if user_token != APP_TOKEN:
        logging.error('failed token [%s]', user_token)
        raise BaseException('404')
    return True


def check_args(args):
    """common checks since 0.3 is passed as a string"""
    blob = args.to_dict()  # otherwise immutable
    # FIX ME - dont return 0 for default values
    blob['threshold'] = coerce.parse_float(args.get('threshold'))
    blob['sample'] = coerce.parse_float(args.get('sample'))
    logging.info('args %s', dumps(blob))
    return blob
