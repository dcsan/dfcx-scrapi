'''
tools for working with graph data formats
'''

import math
import logging

from cxutils.graph.graph_test_data import cyto_graph

flow_colors = {
    'BILL': 'blue',
    'Default Start Flow': 'green'
}


def clean_label(label, counter):
    '''remove extra wording'''
    # label: str = row['label']
    if not label:
        logging.error('item has no label')
        label = 'NONE'
    label = label.replace('head_intent.', '')
    clean = f'{label} ({counter})'
    return clean


def calc_weight(total, nodetype):
    '''logarithmic sizes'''
    if nodetype == 'link':
        multi = 2  # cuberoot/square root etc.
        minimum = 1
        maximum = 25
    else:
        # node
        multi = 1.5    # sqrt smaller is larger
        minimum = 20
        maximum = 100

    weight = (total ** (1./multi))
    weight = max(weight, minimum)
    weight = min(weight, maximum)

    return weight


def links_to_cyto(links, nodes, testdata=True):
    if testdata:
        elements = cyto_graph
        return {'elements': elements}

    edges = []
    nodes_after = []
    # nodes = []
    node_names = []  # simple names
    idx = 0

    for node in nodes:
        node['id'] = node['page']
        node['label'] = clean_label(node['page'], node['total'])
        node['weight'] = calc_weight(node['total'], 10),
        node['shape'] = 'square'
        node['color'] = flow_colors.get(node['flow'], 'blue')
        elem = {
            'data': node
        }
        node_names.append(node['page'])
        nodes_after.append(elem)

    def check_nodes(link, direction):
        '''check source and target exist in nodes'''
        name = link[direction]
        if name in node_names:
            # TODO -increase count
            return
        else:
            node_names.append(name)
            node = {
                'data': {
                    'id': name,
                    'label': clean_label(name, link['total']),
                    'weight': calc_weight(link['total'], 'node'),
                    'shape': 'square',
                    'color': 'blue'
                }
            }
            nodes_after.append(node)

    for idx, link in enumerate(links):
        idx += 1
        # link['id'] = f'link_{idx}'
        # link['label'] = clean_label(link['intent'], link['total'])
        link['label'] = link['total']
        link['color'] = 'black'  # font color?
        link['weight'] = calc_weight(link['total'], 'link'),
        item = {
            'data': link
        }
        edges.append(item)
        check_nodes(link, 'source')
        check_nodes(link, 'target')

    elements = nodes_after + edges  # append
    return {
        'elements': elements
    }
