"""
building and looking through conversation graphs

mostly working with neo4j queries
see chat_graph for bigquery based lookups

"""

from cxutils.format import formatter
from re import sub
import pandas as pd
from py2neo import Graph, Node, Relationship
from py2neo.bulk import merge_nodes

import logging

from cxutils import biglib
from cxutils.digger.chat_log import ChatLog
from cxutils.storage import neolib
from cxutils.dclib import dclib

from icecream import IceCreamDebugger
ic = IceCreamDebugger(prefix='[convo_graph]')


class ConvoGraph():
    """walking conversation graphs with neo4j"""

    def __init__(self, set_name):
        self.set_name = set_name
        self.df = None
        # self.graph = neolib.neo_connect()
        self.py2_conn = neolib.py2_connect()
        self.chat_log = None
        self.table_id = biglib.make_table_id('chat_logs')

    def graph_run(self, query):
        result = neolib.py2_run(query)
        return result
        # result = neolib.raw_query(query)
        # return result
        # self.graph.run(query)

    def load_bq(self):
        self.chat_log = ChatLog(set_name=self.set_name)
        self.df = self.chat_log.fetch_bq()
        return self.df

    def reset_neo(self):
        query = 'match (n) detach delete n'
        neolib.run_query(query)
        # neolib.run_query(
        #     """CREATE CONSTRAINT
        #         uSource
        #         if not exists
        #         ON (m:route) ASSERT m.source IS UNIQUE""")
        # neolib.run_query(
        #     """CREATE CONSTRAINT
        #     uTarget
        #     if not exists
        #     ON (m:route) ASSERT m.target IS UNIQUE""")

    def add_edges_from_bq(self):
        """read all unique transitions"""
        query = f"""SELECT
            page,
            re_match,
            flow,
            max(start_page) as start_page,
            min(start_flow) as start_flow,
            max(intent) as intent,

            count(*) as weight
            FROM {self.table_id}
            where set_name='{self.set_name}'
            group by re_match, page, flow
        """
        rows = biglib.query_list(query)
        total = len(rows)
        for index, row in enumerate(rows):
            # neo4j is taking the 'name' as the unique constraint here
            p1_name = ConvoGraph.flow_page_name(
                page=row['start_page'], flow=row['start_flow'])
            p2_name = ConvoGraph.flow_page_name(row=row)
            re_match = row['re_match'] or "NONE"  # some cyclic nodes?
            re_match = ConvoGraph.short_name(re_match)
            weight = row['weight']
            label = f'[{weight}]-{re_match}'
            flow = row['flow']  # end flow

            # n1 = Node('page', name=p1_name, type='page',
            #           flow=row['start_flow'])
            # n2 = Node('page', name=p2_name, type='page', flow=flow)

            # route = Node('route', type='route', name=re_match, flow=flow,
            #              source=p1_name, target=p2_name)

            query = """
            MATCH
                (n1:page),
                (n2:page)
            WHERE
                n1.cname = $p1_name
            AND
                n2.cname = $p2_name
            CREATE (n1)-[r:route]->(n2)
            SET
                r.label = $label,
                r.type = 'route',
                r.weight = $weight
            """

            neolib.run_query(query,
                             p1_name=p1_name,
                             p2_name=p2_name,
                             re_match=re_match,
                             start_flow=row['start_flow'],
                             end_flow=flow,
                             label=label,
                             weight=weight
                             )
            dclib.log_mod(
                index, 250, f"insert route {index}/{total} query: {query} ")

    @staticmethod
    def flow_page_name(page=None, flow=None, row=None):
        flow = flow or row['flow']
        if flow == 'Default Start Flow':
            flow = 'DSF'
        page = page or row['page']
        cname = dclib.make_cname(page)
        cname = ConvoGraph.short_name(cname)
        cname = f"{flow} {cname}"  # use space for line-break
        return cname

    @staticmethod
    def short_name(cname):
        cname = cname.replace('head_intent.', 'hed ')
        return cname

    @staticmethod
    def split_path(path, node_type='page', edge_type='route'):
        """extract nodes and edges"""
        items = [p for p in path if isinstance(p, dict)]
        nodes = [p for p in items if p.get('type') == node_type]
        edges = [p for p in items if p.get('type') == edge_type]
        return {
            'nodes': nodes,
            'edges': edges
        }

    def load_pages_from_bq(self):
        """update counts on all pages and make sure the final link exists"""

        # seems to skip a bunch of items >.<
        # def insert_pages(rows):
        #     g = neolib.py2_connect()
        #     merge_nodes(g.auto(), rows,
        #                 merge_key=('cname'), labels=['node'])
        #     count = g.nodes.match("page").count()
        #     logging.info('inserted: %s pages from rows:%s', count, len(rows))

        def insert_pages(rows):
            for index, row in enumerate(rows):
                dclib.log_mod(index, 50, f'add page {index}/{len(rows)}')
                # print('row', row)
                cname = ConvoGraph.flow_page_name(row=row)
                q = """merge (:page{cname: $cname})"""
                neolib.run_query(q, cname=cname)
                q = """match (p:page{cname: $cname})
                    SET
                        p.weight=$weight,
                        p.flow=$flow,
                        p.page=$page,
                        p.type='page'
                    """

                # // p.intent=$re_match,
                # // p.escalated=$escalated,
                # // p.operator=$operator

                row.update({'cname': cname})
                neolib.run_query(q, **row)

        # the end pages
        q1 = f"""SELECT
            page, flow,
            concat(page, '-', flow) as cname,
            count(page) as weight
            FROM {self.table_id}
            where set_name='{self.set_name}'
            group by page, flow
        """
        rows = biglib.query_list(q1)
        insert_pages(rows)

        # the start pages
        q2 = f"""SELECT
            start_page as page,
            start_flow as flow,
            concat(start_page, '-', start_flow) as cname,
            count(page) as weight
            FROM {self.table_id}
            where set_name='{self.set_name}'
            group by start_page, start_flow
        """
        rows = biglib.query_list(q2)
        insert_pages(rows)

    @staticmethod
    def limit_weights(path, pmin=10, pmax=100):

        weights = [n['data'].get('weight') or 1 for n in path]
        if weights:
            big = max(weights)
        else:
            big = 0
        for p in path:
            weight = p['data'].get('weight') or 1
            p['data']['weight'] = (pmax * weight / big) + pmin
        return path

    @staticmethod
    def add_flow_colors(path):
        colors = {
            'BILL': 'red',
            'P2P': '#ccea90',
            'Default Start Flow': 'yellow'
        }

        for p in path:
            flow = p['data'].get('flow')
            color = colors.get(flow) or 'grey'
            p['data']['color'] = color
        return path

    def path_from(self, start_page, flow='BILL'):

        q6 = """
            MATCH path =
                (n1:page)
                -[*..5]->
                (n2:page {flow: $flow })
                WHERE
                    n1.cname = $start_page
                WITH
                    n1 AS startPage,
                    [p IN relationships(path) | properties(p)] AS edges,
                    n2 AS endPage,
                    path as path
            RETURN path
            ORDER BY edges[0].weight DESC
            LIMIT 20
        """

        result = neolib.get_cursor(q6, start_page=start_page, flow=flow)
        # path = result.get('path')
        g = result.graph()
        logging.info('graph %s', g)
        # result = neolib.get_cursor(q3, start_page=start_page, flow=flow)
        # data = result.data()
        # path = data[0]
        # count = len(data)
        # print('len data', len(data))
        # paths = []
        # nodes = []
        # edges = []
        path = []

        for e in g.relationships:
            # path.append({'group': 'nodes'})
            for n in g.nodes:
                data = dict(n)
                data['id'] = n.id
                path.append({
                    'data': data
                })

            # path.append({'group': 'edges'})
            # edge_nodes = []
            # for n in e.nodes:
            #     node = {
            #         'id': n.id,
            #     }
            #     node.update(dict(n))
            #     nodes.append({'data': node})
            #     # have to track both nodes on this edge
            #     edge_nodes.append(node)
            points = [n.id for n in e.nodes]
            edge = {
                'id': e.id,
                'source': points[0],
                'target': points[1],
            }
            edge.update(dict(e))
            path.append({'data': edge})

        path = ConvoGraph.limit_weights(path)
        path = ConvoGraph.add_flow_colors(path)

        data = {
            'elements': path
        }

        # elements = {
        #     'elements': {
        #         'nodes': nodes,
        #         'edges': edges
        #     }
        # }
        print(formatter.dumps(data))
        return data
