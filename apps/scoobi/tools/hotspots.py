import logging
import sys
from lib.configlib import ConfigLib
from lib.data.biglib import BigLib


class Hotspot:
    table_id: str

    @classmethod
    def configure(cls):
        '''shared config setup'''
        # table_name = 'feedback_annotations'
        table_name = 'fbl_raw'
        # BigLib.debug = True
        Hotspot.table_id = BigLib.make_table_id(table_name)

    @classmethod
    def get_no_matches(cls, limit=1000):
        logging.warning('start')
        fields = 'page_display_name,content,intent_display_name,intent_confidence_score'
        qs = f'''
            select {fields}
            from {cls.table_id}
            where
                role='END_USER'
                and content is not NULL
            order by
                page_display_name
            limit {limit}
        '''
        df = BigLib.query_df(qs)
        return df

    @classmethod
    def group_no_matches(cls):
        qs = f'''
        select
            count (content) as count,
            page_display_name,
            content,
            max(role) as role
        from {cls.table_id}
        where
            role='END_USER'
        and
            content is not NULL
        and
            page_display_name is not NULL
        group by content, page_display_name
        order by count desc
        '''
        return BigLib.query_df(qs)

    @classmethod
    def group_calls(cls, limit=100):
        qs = f'''
        select
            # session_id,
            position,
            entry_flow_display_name,
            page_display_name,
            intent_display_name,
            match_type,
            role,
            content,

        from {cls.table_id}
        order by
            session_id, position
        limit {limit}'''
        return BigLib.query_df(qs)
