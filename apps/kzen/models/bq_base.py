'''base class for BQ backed types'''


class BqBase:
    '''base functions to read/write to bigquery'''

    def __init__(self, config=None):
        self.config = config
