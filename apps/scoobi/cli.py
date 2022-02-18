from tools.logger import logger  # do this first to set logging format
from tools.viz.sankey import Sankey

import logging

import pandas as pd

# Cli.initial(sprint=19)
# Cli.initial()

# Installer.dump_schemas(config)
# Cli.testing()
from lib.data.biglib import BigLib

from config.client_config import clientConfig
from router.base_router import BaseRouter
from tools.digby.ingester import Ingester
from tools.installer import Installer
from lib.util.text_util import TextUtil


class Cli:
    @classmethod
    def ingest_data(cls, config, fname=None, dataset_display_name=None, sprint_number=26):
        BigLib.configure(config)
        BaseRouter.setup(config)

        # Installer.create_tables(config)
        fpath = 'data/ignored/' + fname

        if dataset_display_name:
            set_name = dataset_display_name
        else:
            if "/" in fname:
                # take just the file name to create a set_name
                fname = fname.split('/')[1]
            set_name = fname.split('.')[0]
            set_name = TextUtil.safe_name(set_name)
            set_name.replace('.', '_')

        logging.info('set_name %s', set_name)
        ingester = Ingester(config=config)
        df = ingester.fetch_csv(fpath)

        # overwrite the temp data
        df['dataset_display_name'] = set_name
        df['current_sprint_number'] = sprint_number
        # df.to_csv()

        where = f'where dataset_display_name="{set_name}" '
        # where = f'where use_case="BILL" and current_sprint_number=23'
        # where = 'where TRUE'
        BaseRouter.process(df, where=where, sample=False, to_sheets=True)

        # BaseRouter.pull(
        #     config=config,
        #     sprint=22,
        #     use_case='BILL',
        #     to_sheets=True,
        #     sample=False)

    @classmethod
    def draw_one(cls, set_name, sprint):
        # fig = draw_one(limit=75, use_case='BILL', sprint=23)
        use_case = 'BILL'
        limit = 100
        print('set_name', set_name)

        fig = Sankey.draw_one(
            # where=where,
            sprint=sprint,
            set_name=set_name,
            use_case=use_case,
            limit=limit,
            # fname=fname
            # use_case='Bill Confusion', fname='xxx-sp19-chat'
        )


config = clientConfig
BigLib.configure(config)


fname = 'client/logfile.csv'  # path from data/ignored
dataset_display_name = 'spXX-client-channel'  # internal to table
sprint_number = 10  # should be set

# Cli.ingest_data(clientConfig, fname=fname,
#                 dataset_display_name=dataset_display_name,
#                 sprint_number=sprint_number)

Cli.draw_one(dataset_display_name, sprint_number)
