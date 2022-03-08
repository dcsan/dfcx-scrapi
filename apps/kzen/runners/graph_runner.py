# from cxutils.storage import neolib
from cxutils.digger import chat_graph
from cxutils.digger.convo_graph import ConvoGraph
from cxutils.digger.chat_graph import ChatGraph

import time


def get_convo():
    set_name = 'meena_0621'
    convo = ConvoGraph(set_name=set_name)
    return convo


def run():
    sankeys()
    # reload_data()
    # get_convo().path_from(start_page='BILL unexpected_charge')


def reload_data():
    # set_name = 'meena_micro'
    # set_name = 'meena_0621'
    set_name = 'sorted_0708'
    convo = ConvoGraph(set_name=set_name)
    convo.reset_neo()
    convo.load_pages_from_bq()
    convo.add_edges_from_bq()
    # convo.load_bq()
    # convo.write_neo()
    time.sleep(5)


def sankeys():
    set_name = 'deets_0710'
    chat_graph = ChatGraph(set_name=set_name)
    links = chat_graph.subgraph('Billing Video')
