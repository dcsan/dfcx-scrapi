"""main for appengine and other tools"""

import logging
# import uuid
from flask import Flask, render_template, request  # escape

from config import configlib
from cxutils.tuner.tuner import Tuner
from cxutils.format import coerce
from cxutils.format.formatter import dumps
from cxutils.digger.chat_graph import ChatGraph
import runner

from server.routes import router
from server.routes import graph_api

# from cxutils import remocon

APP_TOKEN = 'runfoo!'
logging.info('using token: %s', APP_TOKEN)

app = Flask(__name__, template_folder='client/build')

logging.info('trying to start')

# keep here


@app.route('/_ah/start', methods=['GET', 'POST'])
def startup():
    """needed for GAE startup"""
    logging.info('handle _ah/start')
    return {
        'status': 'OK',
        'msg': 'boot'
    }


app.add_url_rule(
    '/api/syscheck',
    methods=['GET'], view_func=router.syscheck)

app.add_url_rule(
    '/api/testone',
    methods=['GET'], view_func=router.testone)


app.add_url_rule(
    '/api/configs/refresh',
    methods=['GET'],
    view_func=router.configs_refresh)


app.add_url_rule('/api/benchmark/run',
                 methods=['GET'],
                 view_func=router.benchmark_run)


app.add_url_rule('/api/tuner/load/intents',
                 methods=['GET'],
                 view_func=router.tuner_load_intents)


app.add_url_rule('/api/tuner/load/phrases',
                 methods=['GET'],
                 view_func=router.tuner_load_phrases)


app.add_url_rule('/api/tuner/load/sims',
                 methods=['GET'],
                 view_func=router.tuner_load_sims)


app.add_url_rule('/api/tuner/scan',
                 methods=['GET'],
                 view_func=router.tuner_scan)


app.add_url_rule('/api/tuner/load/sankey',
                 methods=['GET'],
                 view_func=router.sankey_stats)


app.add_url_rule('/api/tuner/load/simset',
                 methods=['GET'],
                 view_func=router.tuner_load_simset)


app.add_url_rule('/api/graph/load',
                 methods=['GET'],
                 view_func=graph_api.graph_load)

app.add_url_rule('/api/graph/page',
                 methods=['GET'],
                 view_func=graph_api.get_page_data)

app.add_url_rule('/api/testdata/reload',
                 methods=['GET'],
                 view_func=router.testdata_reload)


app.add_url_rule('/api/config/agents',
                 methods=['GET'],
                 view_func=router.config_agents)


app.add_url_rule('/api/config/gdocs',
                 methods=['GET'],
                 view_func=router.config_gdocs)

app.add_url_rule('/api/cron/goldset',
                 methods=['GET'],
                 view_func=router.cron_goldset)


@app.route('/')
def root():
    # last route
    """root of the GAE project"""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4000, debug=True)
