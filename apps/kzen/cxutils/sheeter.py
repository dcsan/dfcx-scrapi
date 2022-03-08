"""read and write convenience for google sheets"""

import time
import logging
from icecream import ic

import gspread
import pandas as pd
from cxutils import customer_opts, logit
from cxutils.format.formatter import dumps
from config import base_config
from config import configlib

ic.configureOutput(includeContext=True)


class Sheeter:
    """gspread wrapper"""

    def __init__(self, cname=None, sheet_id=None, creds_path=None):
        """set up for read/write google sheet
        user can pass a cname OR a sheet_id

        args:
            cname: the cname key to look up sheet_id in configlib
            sheet_id: pass in a direct sheet_id from the URL
            creds_path: where to find creds eg if a different GCP project
        """
        self.creds_path = creds_path or base_config.read('DEFAULT_CREDS_PATH')
        logging.info('getting sheet_id from cname=[%s]', cname)
        if not sheet_id:
            try:
                doc_info = configlib.get_gdoc_info(cname)
                tabname = doc_info['tabname']
                sheet_id = doc_info['sheet_id']
            except KeyError as err:
                logging.error('cannot find sheet cname: [ %s ]', cname)
                # logging.error('gdcocs %s', configlib.fetch_gdoc_configs())
                raise err
            self.docinfo = {
                'cname': cname,
                'sheet_id': sheet_id,
                'tabname': tabname,
                'creds_path': self.creds_path
            }
        else:
            self.docinfo = {
                'cname': cname,
                'sheet_id': sheet_id,
                'tabname': None,  # wait to be called with a tabname later
                'creds_path': self.creds_path
            }

        # ic(self.docinfo)
        self.gsp = gspread.service_account(filename=self.creds_path)
        self.gdoc = self.gsp.open_by_key(sheet_id)

    # def load_summary(self):
    #     summary = pd.read_csv('cases/silver-set/results/summary.csv', header=0)
    #     return summary

    def get_tab_id(self, tabname: str):
        """get tab handle
        args:
            tabname: string
        returns:
            tab: tab handle to use for other commands
        """
        tabname = tabname or self.docinfo['tabname']
        if not tabname:
            raise ValueError('sheet.get_tab_id needs a tabname')
        try:
            tab = self.gdoc.worksheet(tabname)
        except gspread.exceptions.WorksheetNotFound as err:
            logging.error('Sheeter.get_tab_id cannot find tab [%s] in sheet cname: %s',
                          tabname, self.docinfo['cname'])
            logging.info('doc_info %s', self.docinfo)
            raise err
        except gspread.exceptions.APIError as err:
            logging.error(
                'gspread API exception for get_tab_id [%s] in ', tabname)
            logging.info('doc_info %s', dumps(self.docinfo))
            raise err
        return tab

    def get_or_create_tab(self, tabname):
        """get a sheet or create new one"""
        try:
            tab = self.gdoc.worksheet(tabname)
        except gspread.WorksheetNotFound as err:
            logging.info('creating tab %s', err)
            tab = self.gdoc.add_worksheet(
                title=tabname, rows="1000", cols="20")
        except gspread.exceptions.APIError as err:
            logging.error(
                'API exception %s failed to get tab \n[%s]', tabname, err)
            logging.info('doc_info \n%s', self.docinfo)
            raise err

        logging.info('got tab %s', tabname)
        return tab

    def update_tab(self, tabname, df):
        """update a tab in a sheet"""
        tab = self.gdoc.worksheet(tabname)
        tab.update([df.columns.values.tolist()] + df.values.tolist())
        print('updated tab', tabname)

    def read_as_dict(self, tabname):
        """return a dict"""
        tab = self.get_tab_id(tabname)
        data = tab.get_all_records()
        return data

    def read_tab(self, tabname: str, retries=0) -> pd.DataFrame:
        """read named tab as dataframe"""
        tab = self.get_tab_id(tabname)
        try:
            data = tab.get_all_values()
        except gspread.exceptions.APIError as err:
            logging.warning(
                'error on Sheeter.read_tab [%s], retrying %s', tabname, retries)
            time.sleep(5)
            if retries > 3:
                logging.error('max retries %s', retries)
                raise err
            else:
                return self.read_tab(tabname, retries=retries + 1)

        df = pd.DataFrame(data[1:], columns=data[0])
        # print('got len(df) %s', len(df))
        # print(df.head())
        return df

    def write_tab(self, tabname, df):
        """write tab back to DF"""
        tab = self.get_or_create_tab(tabname)
        print('writing', df.head(3))
        # needed or the write fails,
        # but this risks converting all types but gspread writes only strings anyway
        df = df.fillna('')
        try:
            tab.update([df.columns.values.tolist()] + df.values.tolist())
        except BaseException as err:
            logging.error('failed to write tab %s', err)
            logging.error('len(df) %s', len(df))
            logging.error('df\n%s', df.head(3))
            # blob = df.to_dict()
            # logit.obj('blob \n%s', blob)
            template = "An exception of type [{0}] occurred.\nArguments: {1!r}"
            message = template.format(type(err).__name__, err.args)
            logging.error(message)
            # raise (err)

    def fetch_data(self, tabname):
        """grab data for testing from sheets to a local CSV file"""
        tab = self.get_tab_id(tabname)
        data = tab.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])

        df['hit'] = df['expect'].apply(customer_opts.is_head_intent)

        df.to_csv(f'public/runs/specs/{tabname}.csv')
        logit.head(df)
        return df

    def fetch_test_data(self):
        """fetch data for golden sets"""
        self.fetch_data('golden_set')
        self.fetch_data('silver_set_v1')
        self.fetch_data('silver_set_v2')
