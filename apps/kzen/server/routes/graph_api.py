import logging
from datetime import datetime

from flask import Flask, render_template, request  # escape

from server.routes import route_utils
from cxutils.digger.chat_graph import ChatGraph
from cxutils.digger.convo_graph import ConvoGraph
# @app.route('/api/graph/load')
from cxutils.format import formatter


def graph1():
    """load a set of sims for one left intent by clicking on sankey"""
    args = route_utils.check_args(request.args)
    set_name = args.get('set_name') or 'bill_0526_sample'
    chat_graph = ChatGraph(set_name)
    graph_data = chat_graph.get_graph()
    logging.info(
        'api/graph/load set_name: [%s] len: %s', set_name, len(graph_data))
    return {
        'api': 'tuner/graph/load',
        'status': 'OK',
        'time': datetime.now(),
        'result': graph_data
    }


def graph2():
    args = route_utils.check_args(request.args)
    set_name = args.get('set_name', "deets_0710")
    flow = args.get('flow', 'BILL')
    # start_page = args.get('start_page') or "BILL unexpected_charge"
    start_page = args.get('start_page', 'DFS hid_dtmf_acctype_filter')
    # set_name = "meena_0621"
    # start_page = "BILL unexpected_charge"
    g = ConvoGraph(set_name=set_name)
    elements = g.path_from(start_page=start_page, flow=flow)
    result = {
        'status': 'ok',
        'data': elements
    }
    logging.info('graph_load.result %s',
                 formatter.dumps(result))
    return result


def graph_load():
    # app.add_url_rule('/api/graph/load',
    args = route_utils.check_args(request.args)
    set_name = args.get('set_name', "0804-ffm")
    page_set = args.get('page_set', "bill")
    threshold = args.get('threshold', 10)
    chat_graph = ChatGraph(set_name=set_name)
    elements = chat_graph.subgraph(flow=page_set, threshold=threshold)

    result = {
        'status': 'ok',
        'data': elements
    }
    # logging.info('graph_load.result %s',
    #              formatter.dumps(result))
    return result


def get_page_data():
    # `/api/graph/pageData?page_name=${pageName}&set_name=${setName}`
    args = route_utils.check_args(request.args)
    set_name = args.get('set_name', "0804-ffm")
    page_name = args.get('page_name', "bill")
    threshold = args.get('threshold', 1)

    chat_graph = ChatGraph(set_name=set_name)
    page_data = chat_graph.page_data(page_name=page_name, threshold=threshold)

    default = {
        'page_name': page_name,
        'set_name': set_name,
        'escalated': 0,
        'no_match': 0,
        'sources': [],
        'targets': []
    }

    default.update(page_data)

    result = {
        'status': 'ok',
        'data': default
    }
    logging.info('result \n%s', formatter.dumps(result))
    return result
