"""
wrapper for Py2Neo api

TODO: wrap with tx https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.Session.write_transaction

"""
from config import base_config
from icecream import IceCreamDebugger
from typing import TypeVar, Union

import logging


# explicitly namespace and import both drivers until we decide which works better
import neo4j
import py2neo

# add logging for neo4j driver
from logging import getLogger, StreamHandler, DEBUG
handler = StreamHandler()
handler.setLevel(DEBUG)
getLogger("neo4j").addHandler(handler)


# from neo4j import GraphDatabase, BoltDriver, Neo4jDriver
# from py2neo import Graph, Node, Relationship
NEOCONFIG = base_config.read('NEOCONFIG')

# py2neo connection
py2_conn = None

# raw neo4j connection
raw_driver = None


ic = IceCreamDebugger(prefix='[neolib     ]')


def neo_connect() -> Union[neo4j.BoltDriver, neo4j.Neo4jDriver]:

    global raw_driver
    if raw_driver:
        # print('reuse driver')
        return raw_driver

    neoconfig = NEOCONFIG
    raw_driver = neo4j.GraphDatabase.driver(
        neoconfig['url'], auth=(
            neoconfig['user'], neoconfig['pass']))
    if raw_driver is None:
        raise BaseException("cannot connect to neo4j")
    else:
        return raw_driver


def get_data(query, **kwargs):
    cursor = get_cursor(query, **kwargs)
    data = cursor.data()
    ic(data)
    return data


def run_query(query, **kwargs):
    neodriver = neo_connect()
    session = neodriver.session()
    try:
        result = session.run(query, kwargs)
        return result
    except neo4j.exceptions.ServiceUnavailable as err:
        logging.error('query failed: %s args: %s', query, kwargs)
        raise err
    finally:
        session.close()
    # with session.begin_transaction() as tx:
    #     tx.run(query, kwargs)


def get_cursor(query, **kwargs):
    # just get data, no cursor
    neodriver = neo_connect()
    session = neodriver.session()
    # logging.info('neoquery %s', query)
    try:
        # with neodriver.session() as session:
        ic(query, kwargs)
        cursor = session.run(query, **kwargs)
        return cursor
        # data = cursor.data()
        # return data

    except neo4j.exceptions.CypherSyntaxError as err:
        logging.error('neo error %s', err)
        logging.error('failed query: %s', query)
        raise err
    except neo4j.exceptions.Neo4jError as err:
        raise err

    # canot close the session as it kills the cursor >.<
    # finally:
    #     logging.info('close session')
        # session.close()


def py2_connect():
    global py2_conn
    if py2_conn:
        return py2_conn
    py2_conn = py2neo.Graph(
        NEOCONFIG['url'],
        auth=(NEOCONFIG['user'], NEOCONFIG['pass']))
    return py2_conn
    # graph.run('UNWIND range(1, 3) AS n RETURN n, n * n as n_sq')


def py2_run(query):
    conn = py2_connect()
    return conn.run(query)

# def testme():
#     g = connect()
#     a = Node("Person", name="Alice", age=33)
#     b = Node("Person", name="Bob", age=44)
#     edge = Relationship.type("KNOWS")
#     g.merge(edge(a, b), "Person", "name")
