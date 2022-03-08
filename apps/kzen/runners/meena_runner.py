"""
quick tool to convert meena sheet into the right JSON format
"""
import logging
import json
import string

from icecream import IceCreamDebugger

from config import configlib
from models.test_set import TestSet
import pandas as pd

from cxutils.sheeter import Sheeter

# from cxutils.testrunner.testrunner import TestRunner

ic = IceCreamDebugger(
    # prefix=''
)


class MeenaCleaner():

    def __init__(self, docname, tabname):
        self.tabname = tabname
        self.docname = docname
        self.sheet: Sheeter = None

    def import_meena(self):
        self.doc_info = configlib.get_gdoc_info(cname=self.docname)
        # logging.info('doc_info: %s', doc_info)
        # self.tabname = self.doc_info['tabname']
        # logging.info('load_gdoc %s / %s', cname, tabname)
        self.sheet = Sheeter(sheet_id=self.doc_info['sheet_id'])

        self.df = self.sheet.read_tab(self.tabname)
        print('before\n', self.df.head(10))

    def fill_prompts(self):
        df = self.df
        rows = []
        prompt = None
        # df = df[0:10]
        for x, row in df.iterrows():
            prompt = row['prompt'] or prompt
            row['prompt'] = prompt

            if row['accept'] == '1' and row['reply'] != "":
                rows.append(row)
            # ic(row.prompt, row.reply)

        # ic(rows)
        after = pd.DataFrame(rows)
        print(after.head(10))
        self.df = pd.DataFrame(rows)
        return rows

    def write_sheet(self):
        tabout = self.tabname + '.clean'
        self.sheet.write_tab(tabname=tabout, df=self.df)

    def clean_phrase(self, text):
        text = text.lower().translate(
            str.maketrans('', '', string.punctuation))
        return text

    def write_json(self, fname='meena_map.json'):
        """grouped by prompt"""
        data = self.df
        # data = self.df[:20]
        data = data[['prompt', 'reply']]
        grouped = data.groupby('prompt')

        blob = {}
        for name, group in grouped:
            name = self.clean_phrase(name)
            blob[name] = list(group['reply'])
        fpath = f'./data/meena/{fname}'
        with open(fpath, 'w') as fp:
            json.dump(blob, fp, indent=2)
        logging.info('wrote json to: %s', fpath)
        # blob = data.to_json(orient='rows')
        # ic(blob)


def run():
    """lets do it"""

    # configlib.refresh_agent_configs()
    configlib.refresh_gdoc_configs()
    meena = MeenaCleaner(docname='meena_v6', tabname='meena_v6')
    meena.import_meena()
    # meena.fill_prompts()
    # meena.write_sheet()
    meena.write_json('meena_map.json')
