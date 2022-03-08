'''utils for text stuff'''

import re


def normalize(text):
    '''standardized way to remove punc, lowercase etc'''
    #     text = re.sub(r'\w+', '', text)
    text = re.sub(r'[^a-zA-Z0-9_ ]', '', text)
    text = text.lower()
    return text
