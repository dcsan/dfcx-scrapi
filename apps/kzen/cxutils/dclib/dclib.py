
import logging
from typing import Dict
from cxutils.format.formatter import dumps


def remove_blank_column_names(df):
    # drop those with empty column names
    if '' in df.columns:
        df.drop([''], axis=1, inplace=True)
    return df


def reorder_columns(df, columns):
    # print('columns before', self.df.columns)
    remain = [col for col in list(df.columns) if col not in columns]
    columns += remain

    # dupes = [col for col in columns if col in columns]
    # uniq = set(columns)
    # TODO - check for dupes without sets, which will reorder - OrderedSet?
    uniq = columns
    try:
        df = df.reindex(uniq, axis=1)
    except ValueError as err:
        logging.error('failed to reorder columns %s',
                      sorted(df.columns))
        logging.info("uniq %s", sorted(uniq))
        raise err

    print('columns after', dumps(df.columns))
    return df


def add_columns(df, colnames):
    for col in colnames:
        if col not in df.columns:
            # create the column but add generic data type
            df[col] = None
    return df


def rename_columns(df, renames: dict[str, str]):
    """logs and DB field names don't match up"""
    # TODO - check if col exists? so we don't replace agent with empty reply
    for before, after in renames.items():
        if after in df.columns:
            logging.warning(
                'tried to rename [%s] => [%s] but column already existed', before, after)

        elif before not in df.columns:
            logging.warning(
                'tried to rename [%s] => [%s] but column does not exist', before, after)

        else:
            col = {before: after}
            df.rename(columns=col, inplace=True)

    return df


def filter_list(items, key, val):
    """simple filter"""
    items = [item for item in items
             if item[key] == val]
    return items


def log_mod(count, modder, msg):
    if count % modder == 0:
        logging.info(msg)


def make_cname(name: str) -> str:
    """make a canonical name"""
    name = name.lower()
    name = name.replace(' ', '_')
    return name
