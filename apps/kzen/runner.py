#!/usr/bin/env python

"""tool to run utility scripts"""

# import uuid
from cxutils.digger.chat_graph import ChatGraph
from cxutils.digger import chat_static
import time
import os
import logging

from icecream import ic

from cxutils.sapiwrap.mega_agent import MegaAgent
from dfcx_scrapi.core.experiments import ScrapiExperiments

from config import configlib
from config import base_config


# from cxutils import logit # format logs before the others do

# from cxutils.updater.kzen import Kzen
from cxutils import biglib
from cxutils import statter
from cxutils.dumper import Dumper
from cxutils.benchmarker.benchmarker import BenchMarker
from cxutils.testrunner.testrunner import TestRunner
from cxutils import gbot
from cxutils import inout
from cxutils.sheeter import Sheeter
from cxutils.exp.exp import Experimenter
from cxutils.tuner.tuner import Tuner
from cxutils.digger.digger import Digger
from cxutils.digger.chat_log import ChatLog
from cxutils.digger.chat_path import ChatPath
from cxutils.digger.chat_stat import ChatStat
from cxutils.digger.chat_funnel_spec import ChatFunnelSpec

from models.test_set import TestSet

logging.basicConfig(
    format='\n[dfcx|] %(levelname)s: %(message)s',
    datefmt='',
    level=logging.INFO,
    # force=True
)


# want to add at the top of the file
# before anything else screws up the format
# but the linter complains


def logenv():
    """logout the environment"""
    env_vars = [
        'GAE_MEMORY_MB'
    ]
    stats = {}
    for item in env_vars:
        stats[item] = os.environ.get(item)
    logging.info("GAE ENV %s", stats)
    return stats


def dedupe(blobs):
    """remove duplicate dict items"""
    return [
        dict(t) for t in {tuple(d.items())
                          for d in blobs}
    ]


def pick(items, fields):
    """pick out certain dict fields in list of dicts"""
    clean = [
        {
            key: item[key] for key in fields
        }
        for item in items
    ]
    return clean


def set_active():
    """set active tag for dashboard"""
    biglib.set_active(active=True)
    biglib.set_active(agent="dc-mm11-clone", active=False)


def rename():
    """modify agent names in bigquery logs"""
    biglib.rename(agent="chatmerge-stdnlu", new_name="chat-bb30-stdnlu")
    # biglib.rename(agent="chat-bb-custnlu", new_name="chat-bb1000-custnlu")
    # biglib.rename(agent="chatmerge-custnlu", new_name="chat-bb30-custnlu")


def tag_run():
    """add tags to a run"""
    biglib.set_tags(tags="voice")
    biglib.set_tags(agent="chat-multiflow-v12", tags="chat")
    biglib.set_tags(agent="chatmon-v01", tags="chat")


def get_stats():
    """basic stats on flows per agent"""
    statter.get_stats()


def benchmark_one():
    """just test the first agent in runs/run_configs"""
    config = configlib.get_agent('dc-chat-mm-dryrun-test-before')
    bmark = BenchMarker(config)
    bmark.run_one_set(sample=False)


def dump_agent(cname):
    """dump intents for managing later"""
    config = configlib.get_agent(cname)
    dumper = Dumper(config)
    results = dumper.dump_agent()
    logging.info('results %s', len(results))
    return {
        'cmd': "dump_agent",
        'status': 'OK',
        'cname': cname,
        'results': results
    }


def dump_intents(agent_name=None,
                 flowname='Default Start Flow',
                 pagename=None,
                 dumpfile=None):
    """extract all intents in scope within a flow/use case"""
    dumpfile = dumpfile or f'public/runs/dumps/{flowname}-intents.csv'

    config = configlib.get_agent(agent_name)
    dumper = Dumper(config)
    intents = dumper.flow_intents(flowname=flowname, pagename=pagename)
    logging.info('intents %s', intents[0:5])
    # logit.obj('head_intents', intents)
    fields = [
        # 'source_flow', 'source_page',
        'intent'
    ]
    clean = pick(intents, fields)
    clean = dedupe(clean)
    clean = sorted(clean, key=lambda x: x.get('intent'))
    # logit.obj('clean', clean)
    inout.dump_dict_csv(
        clean,
        fields=fields,
        dumpfile=dumpfile
    )
    logging.info('dumped agent_name %s intents to %s', agent_name, dumpfile)


def dump_flow(flowname='HID', agent_name='qa-AGENT-ID'):
    """dump flows/pages/intents for an agent"""
    config = configlib.get_agent(agent_name)
    dumper = Dumper(config)
    # print(dumper.flow_names())
    dump_path = f'public/runs/dumps/{flowname}-flow'
    dumper.dump_flow_by_name(flowname)
    # logit.obj('dump', dump)
    print('dumped to ', dump_path)


def dump_phrases(agent_name):
    """dump all TPs in an agent"""
    config = configlib.get_agent(agent_name)
    dumper = Dumper(config)
    dumpfile = 'public/runs/dumps/phrases.csv'
    dumper.dump_phrases(dumpfile=dumpfile)
    # logit.obj('dump', dump)
    logging.info('dumped phrases to: %s', dumpfile)


def get_agent_stats(agent_name=None):
    """find details on an agent"""
    config = configlib.get_agent(agent_name)
    creds_path = config['creds_path']
    logging.info('config %s', config)
    agent = MegaAgent(creds_path, agent_path=config['agent_path'])
    logging.info('agent stats %s', agent.stats())
    # logit.obj('webhooks', agent.webhooks() )
    # testrunner = TestRunner(config)
    # print(testrunner.agent)


def dump_bill_intents():
    """dump intents just for bill first page"""
    dump_intents(
        agent_name='AGENT-ID',
        flowname='BILL',
        pagename='BILL',
        dumpfile='public/runs/dumps/bill-head-intents.csv'
    )


def dump_head_intents():
    """dump intents for head intent of main flow"""
    dump_intents(
        agent_name='AGENT-ID',
        flowname='Default Start Flow',
        pagename='Default Start Flow',
        dumpfile='public/runs/dumps/head-intents.csv'
    )


def check_dashboard():
    """message in runs"""
    gbot.notify(f"check the <{base_config.read('dashboard_url')}|dashboard>")


# def test_bill():
#     """run a single yaml test"""
#     # config = configlib.get_agent(agent_name='AGENT-ID')
#     testscript = 'BILL'
#     tester = TestRunner()
#     tester.run_story(testscript)


def fetch_tests(storyname):
    """get test spec from google sheet"""
    gdoc = Sheeter(cname='test_runs')
    df = gdoc.read_tab(storyname)
    fpath = f'public/runs/stories/{storyname}.csv'
    df.to_csv(fpath, index=False)
    logging.info('fetched tests [%s] to %s', storyname, fpath)
    return df


def fetch_gtab(doc_id, tab_name):
    """get test spec from google sheet"""
    gdoc = Sheeter(sheet_id=doc_id)
    df = gdoc.read_tab(tab_name)
    df.to_csv(f'public/runs/sheets/{tab_name}.csv', index=False)
    return df


# def run_many_tests():
#     '''run a few tabs of tests in testrunner'''
#     tester = TestRunner()
#     results = tester.run_many_tests()
#     return {
#         'cmd': "run_many_tests",
#         'status': 'OK',
#         'results': results
#     }


def testone(tabname, sheet_key=None, _cached=False):
    """run a single named tab sheet of tests"""
    logging.info('testone=> tabname: %s | sheet_key: %s', tabname, sheet_key)
    options = {
        'sheet_key': sheet_key
    }
    tester = TestRunner(options)
    msg = tester.run_one_tab(tabname, sheet_key)
    return msg


def test_loop(tabname, count=10):
    """
    run a single named tab count times
    dont output results to google doc
    use cached read from google doc
    for speed and avoid api limits
    """
    print('tabname', tabname)
    logging.info('testone: %s', tabname)
    tester = TestRunner()
    msg = ""
    for idx in list(range(count)):
        logging.info('\n\n-- run: %s', idx)
        msg = tester.run_one_tab(tabname, cached=True)
        time.sleep(1)

    return {
        'cmd': "testone",
        'status': 'OK',
        'tabname': tabname,
        'msg': msg,  # just last one?
        'count': count
    }


def list_flow_maps(agent_name):
    """ we need to find page names and intent names for a full flow
        in order to dump the logs effectively via Plx script
    """
    config = configlib.get_agent(agent_name)
    flows = ['BILL', 'AMNT']
    dumper = Dumper(config)
    for name in flows:
        # dump_path = f'public/runs/dumps/{name}-flow'
        # dumps JSON, YAML, CSV
        dumper.dump_flow_by_name(name)
        logging.info('dumped flow all formats %s', name)
    return dumper


def cleanup():
    """delete a run based on agent name"""
    biglib.remove_run(agent='CHID-Chat-MF-Benchmark-adv')
    biglib.remove_run(agent='CHID-Chat-MF-BasicMerge-cus')
    biglib.remove_run(agent='CHID-Chat-MF-BasicMerge-adv')
    biglib.remove_run(agent='CHID-Chat-MF-Benchmark-adv')


def load_test_set_gdoc(set_name):
    """load gdoc into bq based on cname of doc in config sheet"""
    test_set = TestSet(set_name)
    _df = test_set.fetch_from_gdoc(set_name)
    result = {
        'status': 'ok',
        'length': len(_df)
    }
    logging.info('reloaded %s', result)
    return result


# def load_test_set(set_name):
#     '''get data from bq'''
#     test_set = TestSet(set_name)
#     df = test_set.fetch_from_gdoc(set_name)
#     logging.info('loaded test_set len: %s', len(df))

# def bench_run(agent_name, set_name: str, sample=None):
#     """run benchmark
#     args:
#         agent_name: the 'cname' of an agent from the kzen configs sheet
#         set_name: the name of the set. This data should already be loaded into BQ
#     """
#     # bmark = BenchRun(agent_name, set_name)
#     return bmark.run(sample=sample)


# -- experiments
def list_experiments(agent_name):
    """poke around experiments"""
    agent_info = configlib.get_agent(cname=agent_name)
    logging.info('agent_info %s', agent_info)

    agent_path = agent_info['agent_path']

    ex_client = ScrapiExperiments(
        creds_path=agent_info['creds_path'],
        agent_path=agent_path
    )

    environment_id = 'xxxxxx-xxxx-xxxxxx'  # base

    ex_client.list_experiments(environment_id=environment_id)


def check_xp():
    """check experiment"""
    print('checking xp')
    exp = Experimenter('xp_bill')
    # exp.load_sheet('xp_bill_results', 'all')
    # exp.check_run()
    exp.fill_intents()


def tuner_scan(left, right, threshold=None, intent=None):
    """scan a set"""
    set_name = left
    tuner = Tuner(set_name)
    return tuner.scan(intent=intent, threshold=threshold)


def tuner_sim_stats(set_name, threshold=None, intent=None):
    """scan a set"""
    tuner = Tuner(set_name)
    return tuner.calc_sim_stats()


def tuner_load_intents(set_name, agent_name, _sample=None):
    """load tuner"""
    tuner = Tuner(set_name, agent_name)
    return tuner.load_intents()


def tuner_load_phrases(set_name, intent):
    """load tuner"""
    tuner = Tuner(set_name)
    return tuner.load_phrases(intent)


def tuner_update_phrases(set_name, intent):
    """load tuner"""
    tuner = Tuner(set_name)
    return tuner.count_sim_phrases(intent)


def tuner_load_sims(uuid):
    sims = Tuner.load_sims(uuid=uuid)
    return sims


def tuner_get_sankey(left, right, threshold):
    tuner = Tuner(left)
    return tuner.get_sankey(right, threshold)

# def tuner_get_simset(set, name, threshold):
#     tuner = Tuner(left)
#     return tuner.get_simset(left, name, threshold)


def dig_logs(set_name):
    """dig through conversations to build paths"""
    digger = Digger(set_name=set_name)
    digger.fetch_bq()
    digger.process()


def import_chatlogs(set_name):
    """import and process chatlogs"""
    chat_log = ChatLog(set_name)
    chat_log.read_gdoc()
    # chat_log.sample(30)
    chat_log.set_meta({
        'xp_name': set_name,
        'sprint': 18
    })
    chat_log.process()
    chat_log.write_bq(delete_first=True)
    chat_log.write_gdoc(tabname=f'{set_name}_clean')


def calc_chat_stats(set_name):
    """group convos and calc paths"""
    chat_stats = ChatStat(set_name)
    chat_stats.summarize()
    chat_stats.write_gdoc(tabname=f'{set_name}_stats')


def calc_chat_paths(set_name):
    chat_paths = ChatPath(set_name)
    chat_paths.summarize()


def calc_graph(set_name):
    graph = ChatGraph(set_name)
    # graph.count_pages()
    # graph.count_edges()
    graph.get_graph()


def prepare_funnels():
    funnel_specs = ChatFunnelSpec()
    funnel_specs.prepare_funnels()


def calc_funnel_stats(set_name):
    funnel = ChatFunnelSpec()
    funnel.check_all_funnels(set_name=set_name, sample=None)
    # funnel.calc_funnel_hits(set_name, funnel_name)
    # funnel.calculate(set_name=set_name, funnel_name=funnel_name)

# --- main is called by `make` to run these scripts from the console


def main():
    """lets do it"""
    ic('start', 1)

    # configs - reload the configs in case changed
    configlib.refresh_agent_configs()
    configlib.refresh_gdoc_configs()
    # biglib.dump_all_schemas()

    ############# graphs and funnels
    # set_name = 'bill_tiny'
    # set_name = 'bill_0610_sample'
    # # set_name = 'allflows_0610_sample'
    # # set_name = 'bill_0526_sample'
    # import_chatlogs(set_name)
    # calc_chat_stats(set_name)
    # prepare_funnels()
    # calc_funnel_stats(set_name, funnel_name='test-funnel')
    # calc_funnel_stats(set_name)

    # calc_graph(set_name)

    # calc_paths('bill_0526')
    # import_chatlogs('bill_0526_sample')
    # calc_paths('bill_0526_sample')
    # calc_chat_stats('bill_0526_sample')

    # load_test_set_gdoc("meena_bill_subset")
    # bench_run(agent_name='xp-wkshp-v01', set_name='meena_bill_subset')

    # testruns

    testone('bill_confusion_voice_wireless',
            sheet_key='bill_confusion_test_att')  # one named tab
    # testone('XP-meena', sheet_key='xp_tests')  # one named tab

    # import_logs('xp1_chatlogs')
    # dig_logs('xp1_chatlogs')

    # check_xp()
    # tuner_scan('BILL-coreset')
    # tuner_sim_stats('BILL-coreset')

    # tuner_load_intents('dc-hid-remap-after', 'test_set_name')

    # biglib.dump_all_schemas()
    # biglib.dump_schema(table_name='runs')

    # testone('MDNs') # one named tab
    # dump_agent('xp-wkshp-v01')

    # testone('XP-WELCOME', 'xp_tests')
    # testone('SANDBOX')

    # get_agent_stats('xp-wkshp-v01')

    # test_loop('XP-WELCOME', count=100) # one named tab

    # list_experiments('dc-abtest-ext-v01')
    # cleanup()

    # Kzen('sales_remap')
    # Kzen('april_mr_dryrun')
    # Kzen('sales_remap_ext')

    # Kzen('bill_silver')
    # Kzen('bill_custom')

    # load_test_set_gdoc('test_set_name')

    # load_test_set_gdoc('sales_remap')
    # bench_run('dc-AGENT-ID-TR', 'sales_remap')

    # load_test_set_gdoc('BILL-coreset')
    # load_test_set_gdoc('debug_set')

    # bench_run('chat-mf-ext', 'agent-assist-true')
    # bench_run('chat-mf-ext', 'agent-assist-false')

    # bench_run('agent-assist-merge', 'agent-assist-true')

    # bench_run('dc-chat-mf-qa-0218-NO-WEBHOOKS', 'debug_set')
    # bench_run('dc-chat-mf-qa-0218-NO-WEBHOOKS', 'GOLD-chat')

    # configlib.refresh_agent_configs()
    # res = run_many_tests()


logenv()

if __name__ == "__main__":
    main()
