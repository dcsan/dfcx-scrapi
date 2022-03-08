'''input and output'''

import csv
import yaml


def load_csv(filename, basepath=None):
    '''load csv story data'''
    if basepath:
        storypath = f'{basepath}/{filename}.csv'
    else:
        storypath = filename
    with open(storypath, 'r') as fd:
        lines = csv.DictReader(fd)
        storydata = list(lines)
        storydata = [s for s in storydata if s]  # remove empty lines
    return storydata


def load_yaml(story_path):
    '''load yaml story data'''
    # logging.info('run story %s', story_path)
    with open(story_path) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        storydata = yaml.load(file, Loader=yaml.FullLoader)
    return storydata


def dump_list_csv(data, fname):
    '''write csv'''
    outpath = f'public/runs/csv/{fname}.csv'
    with open(outpath, 'w') as fd:
        csv.DictWriter(fd, data)


def dump_dict_csv(obj, dumpfile, fields=None):
    '''dump a dict to csv with header and optional named fields'''
    fields = fields or obj[0].keys()
    with open(dumpfile, 'w') as fd:
        out = csv.DictWriter(fd, fields, extrasaction='ignore')
        out.writeheader()
        out.writerows(obj)
