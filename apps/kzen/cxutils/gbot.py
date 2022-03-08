'''Sending basic bot event to google chat
# https://developers.google.com/hangouts/chat/reference/message-formats/basic
'''

# pylint: disable=line-too-long
# the config paths cannot be line wrapped

import json
import logging
# from google.appengine.api import app_identity
from google.appengine.api import mail
# import webapp2

from httplib2 import Http

# TODO - replace
rooms = {
    #  benchmark
    'benchmark': 'https://chat.googleapis.com/v1/spaces/XXXXX',
    'cron_hook': 'https://chat.googleapis.com/v1/spaces/XXXXX',
    'chat-hid-merge': 'https://chat.googleapis.com/v1/spaces/XXXXX'
}


DEFAULT_BOT = 'benchmark'
# DEFAULT_BOT = 'botbox'  ## annoy others


def send_obj(blob, room=DEFAULT_BOT):
    '''send a json blob'''
    text = json.dumps(blob, indent=2)
    text = f"```{text}```"
    notify(text, room)


def send_mail(opts):
    sender_address = 'USERNAME@google.com'
    return
    # doesnt work
    # mail.send_mail(sender=sender_address,
    #                to=opts['to'],
    #                subject="BenchMarky Update",
    #                body=opts['body']
    #                )


def notify(text, opt=None, room=DEFAULT_BOT, obj=None):
    '''send a message to a chat bot'''

    if obj:
        text += '\n' + json.dumps(obj)

    url = rooms[room]

    # button_msg = {
    #     "textButton": {
    #         "text": "VISIT WEBSITE",
    #         "onClick": {
    #             "openLink": { "url": "http://site.com" }
    #         }
    #     },
    #     # 'text': text
    # }

    # para = {
    #     "text": 'some text'
    # }

    # msg = {
    #     "text": "<https://google.com|link>"
    # }

    # link = {
    #     "url": 'https://google.com'
    # }

    if opt:
        text = f'{text} \n{opt}'

    msg = {
        'text': text
    }
    logging.info(text)

    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}

    http_obj = Http()

    response = http_obj.request(
        uri=url,
        method='POST',
        headers=message_headers,
        body=json.dumps(msg, indent=2),
    )


def error(text, opt, obj=None):
    msg = f"## KZEN ERROR ##\n{text}"
    notify(msg, opt, obj)
    return msg


def fatal(text, opt=None, obj=None):
    error(text, opt, obj)
    # notify(f'## ERROR: {msg}')
    # raise ValueError(msg)


if __name__ == '__main__':
    notify('test message', room='botbox')
