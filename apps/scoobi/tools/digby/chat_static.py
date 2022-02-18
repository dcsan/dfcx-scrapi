"""
Static items in chat
todo - read from google sheet

    driver_intents
        hand curated list of "DRIVER" intents
        handling lookups
    flow_pages
        look up which page in which flow
"""

# import logging
from typing import List, Union
import pandas as pd


class ChatStatic:
    """find the 'driver' for a conversation"""

    filter_pages = [
        'End Session'
    ]

    ignore_drivers = [
        'Operator',
        "No Match",
        "No Input",
        "Direct Intent",
        "Operator",
        "confirmation.yes",
        "support.repeat",
        "confirmation.no",
        "confirmation.wait",
        "support.thankyou",
        "Parameter Filling"
        # "MainMenu",11
    ]

    general_intents: List[str] = [
        'hid.GeneralHelp',
        'hit.GeneralService',
        'Default Welcome Intent',
        'Operator',
    ]

    intent_drivers: List[str] = [
        "hid.intent-1",
        "hid.intent-2",
        "hid.intent-3",
    ]

    bill_pages: List[str] = [
        "page-1",
        "page-2"
    ]

    @staticmethod
    def first_driver(intent: str) -> Union[str, None]:
        """exit on first found driver since they're sorted by frequency"""
        for driver in ChatStatic.intent_drivers:
            if intent == driver:
                return driver
        if intent in ChatStatic.ignore_drivers:
            return None
        return intent

    @staticmethod
    def find_first(df: pd.DataFrame, matches=None) -> Union[str, None]:
        """find first matching driver in a dataframe convo with 'intent' column"""
        matches = ChatStatic.intent_drivers
        for _index, item in df.iterrows():
            # show('item', item)
            if item['intent'] in matches:
                return item['intent']
        return None

    @staticmethod
    def is_intent_detail(intent: str = '') -> Union[str, None]:
        if intent == None or len(intent) == 0:
            return None
        if intent in ChatStatic.ignore_drivers:
            return None
        if intent in ChatStatic.general_intents:
            return None
        return intent
