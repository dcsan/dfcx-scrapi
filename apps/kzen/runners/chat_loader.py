"""
runner for CUSTOMER project
"""
from cxutils import biglib
from icecream import IceCreamDebugger

from config import configlib

from cxutils.digger.chat_funnel_spec import ChatFunnelSpec
from cxutils.digger.chat_stat import ChatStat
from cxutils.digger.chat_path import ChatPath
from cxutils.digger.chat_log import ChatLog
from cxutils.digger.funnels.simple_funnel import SimpleFunnel
from cxutils.dclib import df_lib

# from cxutils.digger.digger import Digger

ic = IceCreamDebugger(
    prefix='vzRunner'
)


def import_chatlogs(set_name, xp_name=None, from_gdoc=True, update_gdoc=True):
    xp_name = xp_name or set_name
    """import and process chatlogs"""
    chat_log = ChatLog(set_name)
    if from_gdoc:
        chat_log.read_gdoc()
    # chat_log.sample(30)
    chat_log.set_meta({
        'xp_name': xp_name,
        'sprint': 18
    })
    # chat_log.light_clean()
    chat_log.process(update_gdoc=update_gdoc)
    chat_log.write_bq(delete_first=True)


def import_convos(cname, set_name):
    chat_stats = ChatStat(set_name)
    chat_stats.read_gdoc(cname=cname)
    chat_stats.write_bq()


def calc_chat_stats(set_name):
    """group convos and calc paths"""
    chat_stats = ChatStat(set_name)
    chat_stats.summarize(update_gdoc=True)
    # chat_stats.dedupe()


def calc_chat_paths(set_name):
    chat_paths = ChatPath(set_name)
    chat_paths.summarize()


def prepare_funnels():
    """for cleaning up info in CUSTOMER funnels"""
    funnel_specs = ChatFunnelSpec()
    funnel_specs.prepare_funnels()


def calc_cust_funnel_stats(set_name):
    funnel = ChatFunnelSpec()
    funnel.check_all_funnels(set_name=set_name, sample=None)
    # funnel.calc_funnel_hits(set_name, funnel_name)
    # funnel.calculate(set_name=set_name, funnel_name=funnel_name)


def funnel_reset(set_name):
    sf = SimpleFunnel(funnel_set='basic', chat_set=set_name)
    sf.reset_all_stats()
    sf.load_funnel_specs_doc()


def simple_funnels(chat_set, funnel_set='basic'):
    sf = SimpleFunnel(funnel_set=funnel_set, chat_set=chat_set, get_gdoc=True)
    sf.check_all_funnels(reset_first=True, funnel_set=funnel_set)
    # sf.check_one(cname='BillingProblemUnhappyPath1', save=True)
    # sf.check_one(cname='BillVideoOperatorFail', save=True)
    # sf.check_one(cname='BillVideoEsc')

# --- main is called by `make` to run these scripts from the console


def load_gs(uri=None):
    uri = 'gs://bucket/file.csv'
    table_id = biglib.make_table_id('temp_table')
    biglib.load_gs(uri, table_id=table_id)
    # job_config = bigquery.LoadJobConfig(
    #     schema=[
    #         bigquery.SchemaField("name", "STRING"),
    #         bigquery.SchemaField("post_abbr", "STRING"),
    #     ],
    #     skip_leading_rows=1,
    #     # The source format defaults to CSV, so the line below is optional.
    #     source_format=bigquery.SourceFormat.CSV,
    # )
    # uri = "gs://cloud-samples-data/bigquery/us-states/us-states.csv"


def process_set(set_name):
    import_chatlogs(set_name)  # raw -> clean
    calc_chat_stats(set_name)  # clean -> stats
    # simple_funnels(set_name)   # funnels calc


def run_x():
    '''load google data storage'''
    df_lib.import_csv()
    # load_gs()


def run():
    """lets do it"""
    ic('chat_loader')

    # configlib.refresh_agent_configs()
    configlib.refresh_gdoc_configs()

    # import_convos(cname='meena_label_y', set_name='meena_label_all')
    # import_convos(cname='meena_label_n', set_name='meena_label_all')

    chat_sets = [
        '0907-log',
    ]

    for chat_set in chat_sets:
        import_chatlogs(chat_set, from_gdoc=True)
        calc_chat_stats(chat_set)
        # simple_funnels(chat_set, funnel_set='bill')
        # simple_funnels(chat_set, funnel_set='daniel')
        # simple_funnels(chat_set, funnel_set='meena')
        # simple_funnels(chat_set, funnel_set='rachels')
        # simple_funnels(chat_set, funnel_set='basic')
