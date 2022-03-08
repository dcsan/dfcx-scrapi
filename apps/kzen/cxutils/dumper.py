'''
for dumping stuff to CSV
'''

import json
import logging
import yaml


from cxutils.sapiwrap.mega_agent import MegaAgent

from dfcx_scrapi.tools.dataframe_functions import DataframeFunctions

# from cxutils import logit
from cxutils import inout

DEFAULT_START_FLOW = 'Default Start Flow'
AGENT_DUMP_PATH = 'public/runs/dumps/agent'


class Dumper:
    '''managing dumps to CSV'''

    def __init__(self, config):
        self.creds_path = config['creds_path']
        self.agent_path = config['agent_path']
        self.agent_id = self.agent_path  # TODO rename in dfcx
        self.agent = MegaAgent(creds_path=self.creds_path,
                               agent_path=self.agent_path)
        self.dffx = DataframeFunctions(creds_path=self.creds_path)
        self.intents_cache = self.agent.list_intents()
        self.flows_cache = self.agent.list_flows()
        self.pages_cache = None  # has to be done for each flow

        logging.info('create dump for %s', config['cname'])

    def get_start_flow(self, flows):
        '''get the start flow assuming the name is as defined in constant'''
        flows = [flow for flow in flows if flow.display_name == DEFAULT_START_FLOW]
        return flows[0]

    def find_intent_by_id(self, intent_id, intents=None):
        '''find intent by id in the cache'''
        intents = intents or self.intents_cache
        # print('looking for id:', intent_id)
        # print('in:', intents[0:2])
        if not intents:
            logging.error('no intents for intent_id: %s', intent_id)
            logging.error('intents: %s', intents)
            logging.error('intents_cache: %s', self.intents_cache)
        items = [item for item in intents if item]  # remove null routes
        items = [item for item in items if item.name == intent_id]
        return items[0]

    def find_flow(self, item_id):
        '''find flow by id in the cache'''
        items = [item for item in self.flows_cache if item.name == item_id]
        if items:
            return items[0]
        else:
            raise KeyError('failed to find flow %s' % item_id)

    def find_page(self, item_id):
        '''find page object by id in the cache'''
        items = [item for item in self.pages_cache if item.name == item_id]
        if items:
            return items[0]
        else:
            last = item_id.split('/').pop()
            # logging.warning('failed to find flow：%s', last)
            return None  # needs to be an object
            # return last
            # raise KeyError('failed to find flow %s' % item_id)

    def logline(self, text):
        '''log single item'''
        print('{}'.format(text))

    def route_info(self, route):
        '''dump route and transitions to json'''
        route_tracker = {}

        if route.intent:
            intent = self.find_intent_by_id(route.intent)
            route_tracker['intent'] = intent.display_name

        if route.condition:
            route_tracker['condition'] = route.condition

        if route.target_flow:
            # self.logline('  [target_flow.id] %s ' % route.target_flow)
            target = self.find_flow(route.target_flow)
            if target:
                route_tracker['target_flow'] = target.display_name

        if route.target_page:
            # self.logline('  [target_page.id] %s ' % route.target_page)
            target = self.find_page(route.target_page)
            if target:
                route_tracker['target_page'] = target.display_name

        if route.trigger_fulfillment:
            fulf = route.trigger_fulfillment
            try:
                text = fulf.messages[0].text.text[0]
                text = text[0:30] + '...'
            except IndexError:
                # logging.warning('failed to get fulfillment text %s', fulf)
                text = None
            # item = {}
            if text:
                route_tracker['text'] = text
            if fulf.tag:
                route_tracker['webhook_tag'] = fulf.tag
            if fulf.set_parameter_actions:
                # this might not get everything
                params = {}
                for param in fulf.set_parameter_actions:
                    params[param.parameter] = param.value
                route_tracker['set.params'] = params
                # logging.warning('check %s', route_tracker)

        # logging.info('route %s', route)
        return route_tracker

    def flow_intents(self, flowname, pagename=None):
        '''get a list of ALL intents in scope on a flow's start page'''
        flow = self.get_flow_by_name(flowname)
        flowdump = self.dump_flow(flow)
        intents = []
        # the keys we'll keep
        keys = [
            'intent', 'target_page', 'target_flow', 'text'
        ]
        flowpages = flowdump['pages']
        if pagename:
            flowpages = [p for p in flowpages if p['page'] == pagename]

        for page in flowpages:
            for route in page['routes']:
                intent = route.get('intent', None)
                if intent:
                    target = {
                        key: route.get(key)
                        for key in keys
                        if route.get(key, False)
                    }
                    target['source_flow'] = flowname
                    target['source_page'] = page['page']
                    intents.append(target)

        return intents

    def dump_agent(self, dump_path=AGENT_DUMP_PATH, limit=False):
        '''dump agent'''
        flows = self.agent.list_flows()
        if limit:
            flows = flows[0:limit]  # sampling
        self.flows_cache = flows

        # blob = json.dumps(flow)
        # print('blob', blob)
        # logging.info('dir flow %s', dir(flow))
        self.logline('agent flows total: %i' % len(flows))
        self.logline('agent intents total: %i' % len(self.intents_cache))

        # flow = self.get_start_flow(flows)

        agent_tracker = {
            'flows': []
        }

        for flow in flows:
            flow_tracker = self.dump_flow(flow)
            agent_tracker['flows'].append(flow_tracker)

        try:
            with open(f'{dump_path}.yaml', 'w') as fp:
                yaml.dump(agent_tracker, fp)

            with open(f'{dump_path}.json', 'w') as fp:
                json.dump(agent_tracker, fp, indent=2)

        except TypeError as err:
            # FIXME TypeError: Object of type RepeatedComposite is not JSON serializable
            logging.error("ERROR! failed to dump agent")
            logging.error("err %s", err)

        return agent_tracker

    def dump_flow(self, flow):
        '''dump the intents in scope at the start of a flow
        useful for building test cases for subflows in a MF agent
        '''
        pages = self.agent.list_pages(flow.name)  # pages within that flow
        pages.append(flow)  # is actually like a page
        self.pages_cache = pages
        start_page = self.dump_page(flow)

        # logging.info('start_page>> %s', start_page)
        dump_path = f'public/runs/dumps/{flow.display_name}'

        flow_tracker = {
            'flow.name': flow.display_name,
            'flow.description': flow.description,
            'pages': [
                start_page
            ]
        }

        logging.info('flow: %s | len start page routes: %s',
                     flow.display_name, len(start_page['routes']))

        for page in pages:
            # logging.info('page: %s', page.display_name)
            page_tracker = self.dump_page(page)
            flow_tracker['pages'].append(page_tracker)

        outfile = f'{dump_path}.yaml'
        logging.info('start dump to %s', outfile)
        try:
            with open(outfile, 'w') as fp:
                yaml.dump(flow_tracker, fp)
            logging.info('yaml dump done %s', outfile)

            with open(f'{dump_path}.json', 'w') as fp:
                json.dump(flow_tracker, fp, indent=2)

            self.dump_flow_csv(flowname=flow.display_name,
                               tracker=flow_tracker, dumpfile=f'{dump_path}.csv')

            logging.info('found %i pages in flow %s',
                         len(pages), flow.display_name)

        except TypeError as err:
            # FIXME TypeError: Object of type RepeatedComposite is not JSON serializable
            logging.error("ERROR! failed to dump %s", flow.display_name)
            logging.error("err %s", err)

        return flow_tracker

    def dump_flow_by_name(self, flowname):
        '''named flow'''
        flow = self.get_flow_by_name(flowname)
        return self.dump_flow(flow)

    def dump_flow_csv(self, flowname, tracker, dumpfile):
        '''dump a flow tracker to a flat file
        usecase | page | intent
        '''
        dumpfile = dumpfile or f'public/runs/dumps/{flowname}-flow.csv'
        rows = []
        for page in tracker['pages']:
            for route in page['routes']:
                row = {
                    'flow': flowname,
                    'page': page['page'],
                    'intent': None,
                    'condition': None,
                    'target': None
                }
                if route.get('target_page'):
                    row['target'] = route.get('target_page')

                if route.get('intent'):
                    row['intent'] = route.get('intent')
                if route.get('condition'):
                    row['condition'] = route.get('condition')
                rows.append(row)

        inout.dump_dict_csv(rows, dumpfile, fields=[
                            'flow', 'page', 'intent', 'condition', 'target'])
        return rows

    def dump_page(self, page):
        '''dump a single page'''
        routes = []
        for route in page.transition_routes:
            route_tracker = self.route_info(route)
            routes.append(route_tracker)
        page_tracker = {
            'page': page.display_name,
            'routes': routes
        }
        logging.info('dump page >> %s | routes: %i',
                     page.display_name, len(routes))
        return page_tracker

    def get_flow_by_name(self, flowname):
        '''based on display_name'''
        # FIXME better filter to not iterate the whole list?
        flows = self.agent.list_flows()

        # agent.flows.list()

        flows = [f for f in flows if f.display_name == flowname]
        return flows.pop()

    def flow_names(self):
        '''list of flow names'''
        flows = self.agent.list_flows()
        names = [f.display_name for f in flows]
        return names

    def dump_phrases(self, dumpfile='public/runs/dumps/phrases.csv'):
        '''dump intents and training phrases for whole agent'''
        intents = self.agent.list_intents()
        # intents = intents[0:4]
        df = self.agent.intents_tracker.intents_to_dataframe(intents)
        df.to_csv(dumpfile, index=False)
        print(df.head(3))
        logging.info('wrote intents and phrases to csv %i rows', len(df))

    def pages(self, flow):
        '''dump pages'''
        pages = self.agent.list_pages(flow)
        logging.info('pages %s', pages)
