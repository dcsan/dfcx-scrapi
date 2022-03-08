import os
import io
import pandas as pd
from google.cloud import storage
import logging

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'config/default-iam-creds.json'


def import_csv(uri=None):
    uri = 'https://drive.google.com/file/d/XXXX/view?usp=sharing'
    path = 'https://drive.google.com/uc?export=download&id=' + \
        uri.split('/')[-2]
    #df = pd.read_pickle(path)
    logging.info('importing path: %s', path)
    df = pd.read_csv(path)
    print(df.head())


def gcp_csv_to_df(bucket_name, source_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    data = blob.download_as_string()
    df = pd.read_csv(io.BytesIO(data))
    print(
        f'Pulled down file from bucket {bucket_name}, file name: {source_file_name}')
    return df
