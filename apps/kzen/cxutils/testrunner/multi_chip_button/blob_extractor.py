import pandas as pd
import json
# from cxutils.testrunner.multi_chip_button.blob_json_reader import start
from blob_json_reader import start

BLOB_EXTRACTOR_PATH = 'cxutils/testrunner/multi_chip_button/'

# setting up config file
with open(f'{BLOB_EXTRACTOR_PATH}config.txt', 'r') as f:
    config = f.read().split('\n')
    input_file = config[0].split(',')[0]
    input_file_sheet = config[0].split(',')[1]
    output_file = config[1].split(',')[0]
    output_file_sheet = config[1].split(',')[1]
    json_file = config[2]

# reading input file & sheet
# xls = pd.read_csv('cxutils/testrunner/multi_chip_button/'+input_file)
df = pd.read_csv(f'{BLOB_EXTRACTOR_PATH}'+input_file)
final_written = None

# output file
# writer = pd.ExcelWriter(output_file)


def to_every_message(row):
    global final_written 
    cell_value = row[0]

    print(cell_value)

    # getting response from core function
    path_list, response_list = start()

    write_list = [(cell_value, "", "")]
    for new_row in zip(path_list, response_list):
        # write_list.append(("setParam","Authentication","{[false]}"))
        write_list.append(("send","text",cell_value))
        write_list.append(("send", "text", new_row[0]))
        # write_list.append(("expect","intent_name",cell_value[1]))
        write_list.append(("expectPayload", "equalTo", new_row[1]))
        write_list.append(("restartAgent","",""))
    if final_written is None:
        final_written = write_list
    else:
        final_written = final_written + write_list


# after reading each yellow lable applying function
df.apply(to_every_message, raw=True, axis=1)

# from dataframes to output excel
df_out = pd.DataFrame(final_written)
df_out.to_csv(f'{BLOB_EXTRACTOR_PATH}' + output_file)
# df_out.to_excel(writer, sheet_name=output_file_sheet, index=None, header=None)
# writer.close()