'''
create all the tables based on schema files eg
docs/
'''
import logging
import json

from config.base_config import BaseConfig
from lib.data.biglib import BigLib


class Installer:

    @staticmethod
    def setup(config: BaseConfig):
        '''call once per session'''
        BigLib.configure(config)

    @classmethod
    def create_tables(cls, config: BaseConfig):
        '''recreate the tables based on schema in the repo'''
        cls.create_table('fbl_raw')
        cls.create_table('chat_logs')
        cls.create_table('convo_logs')
        # cls.check_schemas()

    @classmethod
    def create_table(cls, table_name):
        schema_path = f'data/schemas/{table_name}_schema.json'
        BigLib.create_table(schema_path, table_name, delete_first=True)

    @classmethod
    def dump_schemas(cls):
        '''dump the schemas from BQ so we can check in to the repo'''
        schemas = [
            'fbl_raw',
            'chat_logs',
            'convo_logs',
        ]
        for table_name in schemas:
            cls.dump_schema(table_name)

    @classmethod
    def dump_schema(cls, table_name):
        '''if schemas have been manually edited
        use this to dump back a .schema file to use for migrations etc'''
        data = BigLib.describe_schema(table_name=table_name)
        fp = f'data/schemas/{table_name}_schema.json'
        blob = json.dumps(data, indent=2)
        # open file for writing, "w"
        with (open(fp, "w") as file):
            file.write(blob)
        logging.info('table: %s df\n %s', table_name, blob)
