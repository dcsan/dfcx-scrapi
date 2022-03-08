"""main for appengine and other tools"""

import json
import logging
from datetime import datetime
# import uuid
from flask import Flask, render_template, request  # escape

from config import configlib
from cxutils.tuner.tuner import Tuner
# from cxutils.format import coerce
from cxutils.format.formatter import dumps
from cxutils import gbot
import runner
from server.routes import route_utils

from cxutils.benchmarker.benchmarker import BenchMarker

logging.info('trying to start')


# @app.route('/api/testone')
def testone():
    """run one test"""
    now = datetime.now()
    stamp = now.strftime("%d/%m/%Y %H:%M:%S")
    logging.info("OK api/testone %s", stamp)
    tabname = request.args.get('tabname')
    sheet_key = request.args.get('sheet_key')
    logging.info('tabname %s', tabname)
    result = runner.testone(tabname, sheet_key)
    result['stamp'] = stamp
    result['tabname'] = tabname
    return result


# @app.route('/api/syscheck')
def syscheck():
    """basic syscheck"""
    msg = {
        'status': 'OK',
        # 'time': datetime.now()
    }
    logging.info('syscheck %s', msg)
    return msg


# @app.route('/api/configs/refresh')
def configs_refresh():
    """pull all configs again from gdocs"""
    logging.info('configs_refresh')
    result = configlib.fetch_all_configs()
    return {
        'status': 'OK',
        'time': datetime.now(),
        'result': result
    }


# @app.route('/api/cron/goldset')
def cron_goldset():
    """runs daily"""
    logging.info('cron goldset')
    configlib.fetch_all_configs()
    agent_name = 'cron_agent'
    set_name = 'cron_gold_set'
    sample = request.args.get('sample')
    msg = f'start cron:\n- agent_name: `{agent_name}`\n- set_name: `{set_name}` \n- sample: `{sample}` '
    gbot.notify(msg, room='cron_hook')
    bmark = BenchMarker(agent_name, set_name, reload=True)
    results = bmark.run_one_set(sample=sample)

    summary = json.dumps(results['summary'], indent=2)
    dashboard_url = 'https://datastudio.google.com/s/ssrY0vgwM6o'
    output = {
        'status': 'OK',
        'time': datetime.now(),
        'rows': len(results['df']),
        'summary': summary,
        'dashboard': dashboard_url
    }
    msg2 = f'result: ```{output}``` \ndashboard {dashboard_url}'
    gbot.notify(msg2, room='cron_hook')
    # gbot.notify(df, room='cron_hook') ## TODO - show summary

    # mail doesnt work
    # opts = {
    #     'to': 'USERNAME@google.com',
    #     'body': msg2
    # }
    # gbot.send_mail(opts)
    # logging.info('cron output %s', output)
    return output


# @app.route('/api/benchmark/run')
def benchmark_run():
    """run BM"""
    agent = request.args.get('agent')
    set_name = request.args.get('test')
    sample = request.args.get('sample')
    logging.info('run BM %s test: %s, sample: %s', agent, set_name, sample)
    bmark = BenchMarker(agent_name=agent, set_name=set_name, reload=True)
    result = bmark.run_one_set(max_intents=1)
    # df = runner.bench_run(agent, set_name=set_name, sample=sample)
    logging.info('bm run finished \n%s')
    response = {
        'api': 'benchmark/run',
        'status': 'OK',
        'time': datetime.now(),
        'length': len(result)
    }
    logging.info('bm run response %s', response)
    return response

# @app.route('/api/tuner/load/intents')


def tuner_load_intents():
    """run BM"""
    agent_name = request.args.get('agent')
    set_name = request.args.get('set_name')
    sample = request.args.get('sample')
    logging.info('run BM %s test: %s, sample: %s',
                 agent_name, set_name, sample)
    result = runner.tuner_load_intents(set_name, agent_name, sample)
    return {
        'api': 'tuner/run',
        'status': 'OK',
        'time': datetime.now(),
        'result': result
    }


# @app.route('/api/tuner/load/phrases')
def tuner_load_phrases():
    """run BM"""
    set_name = request.args.get('set_name')
    # sample = request.args.get('sample')
    intent = request.args.get('intent')
    result = runner.tuner_load_phrases(set_name, intent)
    return {
        'api': 'tuner/run',
        'status': 'OK',
        'time': datetime.now(),
        'result': result
    }


# @app.route('/api/tuner/load/sims')
def tuner_load_sims():
    """load similar items for one uuid"""
    uuid = request.args.get('uuid')
    result = runner.tuner_load_sims(uuid)
    return {
        'api': 'tuner/run',
        'status': 'OK',
        'time': datetime.now(),
        'result': result
    }


# @app.route('/api/tuner/scan')
def tuner_scan():
    """scan for similar items items between two sets"""
    args = route_utils.check_args(request.args)
    left = args.get('left')
    # right = args.get('right')
    threshold = args.get('threshold')
    intent = args.get('intent')
    model_type = args.get('model_type')

    tuner = Tuner(set_name=left)
    result = tuner.scan(
        intent=intent,
        threshold=threshold,
        model_type=model_type)

    # logging.info('router threshold %s', threshold)
    # result = runner.tuner_scan(
    #     left=left,
    #     right=right,
    #     threshold=threshold,
    #     intent=intent)
    return {
        'api': 'tuner/run',
        'status': 'OK',
        'time': datetime.now(),
        'result': result
    }


# @app.route('/api/tuner/load/sankey')
def sankey_stats():
    """scan for problems"""
    args = route_utils.check_args(request.args)
    left = args.get('left')
    right = args.get('right')
    threshold = args.get('threshold')
    result = runner.tuner_get_sankey(left, right, threshold)
    logging.info('sankey_stats \nlen: %s', len(result))
    return {
        'api': 'tuner/run',
        'status': 'OK',
        'time': datetime.now(),
        'result': result
    }


# @app.route('/api/tuner/load/simset')
def tuner_load_simset():
    """load a set of sims for one left intent by clicking on sankey"""
    args = route_utils.check_args(request.args)
    left = args.get('left')
    set_name = args.get('set_name')
    threshold = args.get('threshold')
    tuner = Tuner(set_name)
    sims = tuner.get_simset(left, threshold)
    logging.info('simset \nlen: %s', len(sims))
    return {
        'api': 'tuner/load/simset',
        'status': 'OK',
        'time': datetime.now(),
        'result': sims
    }


# @app.route('/api/testdata/reload')
def testdata_reload():
    """run BM"""
    test = request.args.get('test')
    result = runner.load_test_set_gdoc(test)
    return result


# @app.route('/api/config/agents')
def config_agents():
    """get agents"""
    blob = configlib.get_agents(form='dict')  # not json
    result = {
        'status': 'ok',
        'data': blob,
        'time': datetime.now()
    }
    logging.info('GET /config/agents => %s', len(result))
    return result


# @app.route('/api/config/gdocs')
def config_gdocs():
    """get gdocs"""
    blob = configlib.get_gdocs(form='dict')
    result = {
        'status': 'ok',
        'data': blob,
        'time': datetime.now()
    }
    logging.info('/api/config/gdocs => %s', len(result))
    return result


# @app.route('/')
# def root():
#     """root of the GAE project"""
#     return render_template('index.html')
