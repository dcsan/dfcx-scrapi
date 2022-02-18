from config.base_config import BaseConfig
from config.shared_config import sharedConfig


# override this with client specific info
clientConfig: BaseConfig = {
    'debug': True,
    'gcp_project': 'XXX-project-name',
    'creds_path': 'config/CREDS-FILE.json',
    'dataset': 'scoobi',

    # use full table.id for these to prevent mistakes across datasets
    'upstream_table_id': 'GCP-PROJECT.dataset.input-table',
    'raw_table_id': 'BQ-DATASETNAME.scoobi.raw_table_name',

    # id of google sheet used for configuation
    'sheets': {
        'ChatParser': 'google-sheet-id'
    }
}

for col in sharedConfig.keys():
    clientConfig[col] = sharedConfig[col]  # type: ignore
