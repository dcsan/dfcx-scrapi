import pandas as pd
import json

BLOB_EXTRACTOR_PATH = 'cxutils/testrunner/multi_chip_button/'

stack_path = []
# root_node = ''
path_list = []
response_list = []


def stack_pop():
    global stack_path
    stack_path.pop()


def add_stack(var):
    global stack_path
    stack_path.append(var)


def show_stack():
    global stack_path
    # print(root_node, ">>", ">>".join(stack_path))
    # path_list.append(root_node + ">>" + ">>".join(stack_path))
    path_list.append(">>".join(stack_path))


# recursive function to implement logic
def p_list(dct1):
    global response_list

    for nodes in dct1:
        if nodes in ['values', 'message', 'components']:
            continue
        else:
            if type(nodes) != dict:
                add_stack(str(nodes))
            else:
                stack_pop()
            tmp = 0
            try:
                tmp = dct1[nodes]['values']
                show_stack()
                response_list.append(dct1[nodes]['message'])
                p_list(dct1[nodes])
                tmp = 0
            except KeyError:

                tmp = 1

            finally:

                if tmp == 1:
                    # print()
                    show_stack()
                    # print(dct1[nodes]['message'])
                    response_list.append(dct1[nodes]['message'])
                    # print("%%%%%%%%%%%%%%%%\n\n")

                    # pop stack
                    stack_pop()

                else:
                    try:
                        p_list(dct1[nodes]["values"])
                    except:
                        pass


def start(file_name= f'{BLOB_EXTRACTOR_PATH}blob.json'):
    global root_node, path_list, response_list
    with open(file_name, 'r', encoding='utf') as f:
        dct = json.loads(f.read())
    # parent_nodes = []
    # for item in dct:
    #     if item in ['values', 'message', 'components']:
    #         continue
    #     parent_nodes.append(item)

    # for nod in parent_nodes:
    #     root_node = nod
    #     p_list(dct[nod])
    # return path_list, response_list
    
    p_list(dct)
    tmp = path_list
    tmp2 = response_list
    path_list = []
    response_list = []
    return tmp, tmp2
