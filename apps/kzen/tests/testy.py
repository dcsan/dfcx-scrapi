"""stuff to make testing a bit easier"""

import logging


class Testy:
    """name spacer"""

    @staticmethod
    def show(msg, df):
        """has to be warning to show during tests"""
        logging.warning('\n\n--- %s\n%s', msg, df)
