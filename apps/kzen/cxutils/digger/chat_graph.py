"""drawing graphs

nodes:
    page_from - is the page when turn started

edges:
    page_from   - source where we start
    page        - target where we end



"""

from cxutils.format import formatter
import logging
from typing import Dict, List
from cxutils import biglib
from cxutils.digger.dig_item import DigItem
from icecream import ic

from cxutils.graph import graph_tools

ic.configureOutput(prefix='ChatGraph |', includeContext=True)

NODE_LIMIT = 18  # limit on query
EDGE_LIMIT = 30  # will remove redundant ones
MIN_NODE_COUNT = 10
MIN_EDGE_COUNT = 25  # if pages dont exist will be removed
NODE_SCALE = 60
EDGE_SCALE = 30

base_options = {
    'skip_loops': False
}

COLOR_NODES = {
    'End Session': 'red',
    'HID DTMF AccType filter': 'green',
    'No Match': 'red',
    'No Input': 'purple',
    'Operator': 'red',
    'Parameter filling': 'red',
    'Default Start Flow': 'green',
    'BILL': 'blue',
}

page_sets = {
    'flow1': [
        'flow1.intent1',
        'flow1.intent2',
    ],
    'start': [
        'Welcome',
        'start.intent1',
    ]
}


class ChatGraph(DigItem):
    """graph of stuff"""

    def __init__(self, set_name, options: Dict = None):
        super().__init__(set_name)
        options = options or {}
        base_options.update(options)  # update FROM custom options
        self.options = base_options
        ic(self.options)
        self.set_name = set_name
        self.chat_logs_table = biglib.make_table_id('chat_logs')

    def count_pages(self):
        """page | count
        if we limit the number of nodes that also removes links
        """

        query = f"""
            SELECT

            page_from as label,
            count(page_from) as count

            FROM `{self.chat_logs_table}`
            where
            set_name='{self.set_name}'

            group by page_from
            order by count desc
            limit {NODE_LIMIT}

        """
        rows = biglib.query_list(query)
        rows = ChatGraph.filter_by_count(rows, MIN_NODE_COUNT)
        pages = self.add_nodes_meta(rows)
        return pages

    def count_edges(self):
        """connections between nodes"""
        query = f"""
            SELECT
            count(page_from) as count,
            page_from as source,
            page as target,
            max(re_match) as label,

            # concat(page_from, '-', page) as label

            FROM `{self.chat_logs_table}`
            where
            set_name='{self.set_name}'

            group by page_from, page
            order by count desc

            limit {EDGE_LIMIT}
        """
        rows = biglib.query_list(query)
        # rows = ChatGraph.filter_by_count(rows, MIN_EDGE_COUNT)
        if self.options['skip_loops'] == True:
            rows = ChatGraph.skip_loops(rows)
        rows = ChatGraph.scale_counts(rows, max_size=EDGE_SCALE)
        for row in rows:
            row['id'] = row['label']
            row['color'] = COLOR_NODES.get(row['label'], 'blue')
            row['label'] = ChatGraph.clean_label(row)
        self.edges = rows
        ic(self.edges)
        return self.edges

    @staticmethod
    def clean_label(row):
        label: str = row['label']
        if not label:
            logging.error('row has no label %s', row)
            # todo why?
            label = 'NONE'
        size = int(row['count'])  # not size since pct is broken
        label = label.replace('head_intent.', '')
        clean = f'{label} | {size}'
        return clean

    @staticmethod
    def skip_loops(items):
        '''remove self loops as it can break some client rendering'''
        # TODO aggregate loop data
        items = [item for item in items
                 if item['source'] != item['target']]
        return items

    @staticmethod
    def scale_counts(items, max_size=100.0):
        """normalize scale of items"""
        biggest = 1
        big_item = None
        for item in items:
            if item['count'] > biggest:
                big_item = item
                biggest = item['count']

        ratio = float(max_size) / biggest
        logging.info('new biggest %s = %s | ratio = %s',
                     big_item, biggest, ratio)
        for item in items:
            count = item['count'] * ratio
            if count < 1:
                count = 1
            item['size'] = count

        # ic(items)
        return items

    @staticmethod
    def filter_by_count(items, count=10):
        """minimum count needed to show in the graph"""
        items = [item for item in items
                 if item.get('count') > count]
        return items

    @staticmethod
    def pages_exist(edge, page_names: List[str]) -> bool:
        """check source and target of edge in pages"""
        source = edge.get('source')
        target = edge.get('target')

        if not source or not target:
            logging.warning('no source or target %s', edge)
            return False

        if not source in page_names:
            logging.warning('source not found [%s] in \n%s', source, edge)
            return False
        if not target in page_names:
            logging.warning('target not found [%s] in \n%s', target, edge)
            return False

        # ic(source, target, True)
        return True

    def get_graph(self):
        """calc the full graph"""
        pages = self.top_pages(limit=NODE_LIMIT)
        edges = self.top_edges(pages)
        # edges = self.count_edges()
        graph = []

        for item in pages:
            # data = item.update()
            node = {
                'data': item
            }
            graph.append(node)

        for item in edges:
            if not (ChatGraph.pages_exist(
                    edge=item, page_names=self.page_names)):
                continue
            edge = {
                'data': item
            }
            graph.append(edge)

        ic(graph)
        return graph

    def top_pages(self, limit):
        query = f'''
            select

            max(start_page) as id,
            count(start_page) as count,
            avg(no_match) as no_match_avg,
            avg(operator) as operator_avg

            FROM `{self.chat_logs_table}`
            WHERE set_name='{self.set_name}'

            group by start_page

            order by count(start_page) desc
            limit {limit}
        '''
        rows = biglib.query_list(query)
        rows = ChatGraph.append_wrap_nodes(rows)
        pages = self.add_nodes_meta(rows, color='blue')
        rows = ChatGraph.scale_counts(rows, max_size=NODE_SCALE)
        self.page_names = [page['id'] for page in pages]
        self.pages = pages
        return pages

    @staticmethod
    def append_wrap_nodes(rows):
        blank_page = {
            'label': 'START',
            'id': '-',
            'count': NODE_SCALE,
        }
        end_page = {
            'label': "End Session",
            'id': 'End Session',
            'count': NODE_SCALE
        }
        rows += [blank_page] + [end_page]
        # rows.append([blank_page, end_page])
        return rows

    def top_edges(self, pages, limit=100):

        # ugly to quote each element, needed for SQL query
        # be nice to have an ORM for BQ
        page_names = [page['id'] for page in pages]
        names = [f'"{name}"' for name in page_names]
        names = ', '.join(names)

        query = f'''
            SELECT
                start_page as source,
                max(re_match) as id,
                page as target,
                count(start_page) as count

            FROM `{self.chat_logs_table}`
            WHERE
                set_name='{self.set_name}'
                and start_page in ({names})
                and page in ({names})

            GROUP BY start_page, page
            order by count(re_match) desc

            # limit {limit}
        '''
        rows = biglib.query_list(query)
        # rows = [row for row in rows if row['count'] > 5]
        rows = ChatGraph.scale_counts(rows, max_size=EDGE_SCALE)
        rows = self.add_nodes_meta(rows, color='black')
        self.edges = rows
        return rows

    def add_nodes_meta(self, rows, color='black'):
        '''add metadata to nodes like color, label from DB output'''
        for row in rows:
            row['color'] = COLOR_NODES.get(row['flow'], color)
            row['label'] = str(row['id'])
            row['label'] = ChatGraph.clean_label(row)

        return rows

    def get_links(self, page, direction='in', threshold=5):
        '''get links in or out of page based on direction'''

        if direction == 'in':
            query = f"""
            SELECT
                # max(page) as page,
                max( start_page ) as other,
                count( start_page ) as total,
                max(re_match) as intent,
                max(flow) as flow
            FROM `YOUR-BQ-DATASET.chat_logs`
            WHERE
                set_name='{self.set_name}'
                and page = "{page}"
            GROUP BY
                page, start_page, re_match
            HAVING
                count(start_page) > {threshold}
            ORDER BY
                count(start_page) desc
            """
        else:

            query = f"""SELECT
                # max(start_page) as page,
                max( page ) as other,
                count( page ) as total,
                max(re_match) as intent,
                max(flow) as flow
            FROM `YOUR-BQ-DATASET.chat_logs`
            WHERE
                set_name='{self.set_name}'
                and start_page = "{page}"
            # ORDER BY
            #     count(page) desc
            GROUP BY
                start_page, page, re_match
            HAVING
                count(page) > {threshold}
            ORDER BY
                count(page) desc

            """

        # query = f"""
        #     SELECT
        #         max( {link_field} ) as other,
        #         count( {link_field} ) as total
        #     FROM `{self.chat_logs_table}`
        #     where
        #         set_name='{self.set_name}'
        #         and start_page = "{page}"
        #     group by start_page, {link_field}
        #     """
        items = biglib.query_list(query)
        links = []

        # now go through and reformat
        for item in items:
            if item['total'] < threshold:
                continue

            self_link = (item['other'] == page)
            if direction == 'in':
                link = {
                    'source': item['other'],
                    'target': page
                }
            else:
                link = {
                    'source': page,
                    'target': item['other']
                }
            link.update({
                'total': item['total'],
                'direction': direction,
                'self_link': self_link,
                'intent': item['intent'],
                'flow': item['flow'],
            })
            links.append(link)
        return links

    def get_nodes(self, links, threshold=25):
        '''collect node names and counts'''
        # logging.info('get_nodes for links %s', links)
        node_names = [node['target'] for node in links]
        node_names_str = [f' "{name}" ' for name in node_names]
        node_names_str = ','.join(node_names_str)
        # node_names_str = ','.join(node_names)
        # node_names_str = ' "meena_dis", "Operator Disambiguation" '
        logging.info('get_nodes %s', node_names_str)

#  SELECT
#     page,
#     count( page ) as total,

#     FROM `YOUR-BQ-DATASET.chat_logs`
#     WHERE
#         set_name='0804-ffm'
#         and page in ('meena_dis', 'Operator Disambiguation')
#     group by page

        query = f"""SELECT
            page,
            count( page ) as total,

        FROM `YOUR-BQ-DATASET.chat_logs`
        WHERE
            set_name='{self.set_name}'
            and page in ( {node_names_str} )
        GROUP BY
            page
        HAVING
            count(page) > {threshold}
        """
        nodes = biglib.query_list(query)
        return nodes

    def xsubgraph1(self, flow='BILL', threshold=10):
        '''build a graph starting from start_page'''
        links = []
        links = self.flow_edges(flow, threshold=threshold)
        # pages = page_sets[page_set]

        # for page in pages:
        #     targets = self.get_links(page=page, direction='out', threshold=10)
        #     links += targets

        nodes = self.get_nodes(links)
        logging.info('nodes %s', nodes)
        # targets = self.get_links(page=page, direction='in', threshold=20)
        # links = targets + sources

        cyto = graph_tools.links_to_cyto(
            links=links, nodes=nodes, testdata=False)
        # logging.info('links from %s => \n %s',
        #              page, formatter.dumps(cyto))
        return cyto

    def flow_nodes(self, flow='BILL', threshold=10):
        '''simple set of links with totals not split by intent'''
        query = f'''
            select
                # start_page,
                page,
                count(page) as total,
                max(flow) as flow,
            from
                YOUR-GCP-PROJECT.YOUR-BQ-DATASET.chat_logs
            where
                set_name='{self.set_name}'
            and flow = '{flow}'
            group by page
            having
                count(page) > {threshold}
            order by count(page) desc

        '''
        items = biglib.query_list(query)
        nodes = []
        # now go through and reformat
        for item in items:
            if item['total'] < threshold:
                continue
            nodes.append(item)
        return nodes

    def flow_edges(self, flow='BILL', threshold=10):
        '''simple set of links with totals not split by intent'''
        query = f'''
            select
                start_page,
                page,
                flow,
                count(page) as total
            from
                YOUR-GCP-PROJECT.YOUR-BQ-DATASET.chat_logs
            where
                set_name='{self.set_name}'
                and flow = '{flow}'
            group by
                start_page, page, flow
            HAVING
                count(page) > {threshold}
            order
                by count(page) desc
        '''
        items = biglib.query_list(query)
        links = []
        # now go through and reformat
        for item in items:
            if item['total'] < threshold:
                continue

            self_link = (item['page'] == item['start_page'])
            item.update({
                'source': item['start_page'],
                'target': item['page'],
                'total': item['total'],
                'self_link': self_link,
                'flow': item['flow'],
            })
            links.append(item)
        return links

    def subgraph(self, flow='BILL', threshold=10):
        '''build a graph starting from start_page'''
        links = []
        links = self.flow_edges(flow=flow, threshold=threshold)
        nodes = self.flow_nodes(flow=flow, threshold=threshold)

        # TODO - add some extra nodes for in/out pages

        cyto = graph_tools.links_to_cyto(
            links=links, nodes=nodes, testdata=False)
        # logging.info('cyto %s => \n %s',
        #              flow, formatter.dumps(cyto))
        return cyto

    def page_data(self, page_name: str, threshold=10):
        targets = self.get_links(
            page=page_name, direction='out', threshold=threshold)
        sources = self.get_links(
            page=page_name, direction='in', threshold=threshold)

        return {
            'targets': targets,
            'sources': sources
        }
