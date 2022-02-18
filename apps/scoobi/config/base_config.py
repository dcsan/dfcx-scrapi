from lib.util.dflib import reorder_columns
from typing import TypedDict


class ActorTypeMap(TypedDict):
    AUTOMATED_AGENT: str
    END_USER: str


class BaseConfig(TypedDict, total=False):
    debug: bool
    gcp_project: str
    creds_path: str
    upstream_table_id: str
    raw_table_id: str
    dataset: str
    rename_columns: dict[str, str]
    reorder_columns: list[str]
    role_type_map: dict[str, str]
    sheets: dict[str, str]
    # table_id: str
    # column_map: dict[str, str]
