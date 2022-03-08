import csv


def dump_csv(data, csv_path):
    with open(csv_path, 'w') as fd:
        fields = data[0].keys()
        csv_writer = csv.DictWriter(fd, fields)
        csv_writer.writeheader()
        csv_writer.writerows(data)
    return csv_path

