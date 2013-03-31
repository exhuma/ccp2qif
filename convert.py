import csv
from collections import namedtuple

DataRow = namedtuple('DataRow',
    'accounting_date, '
    'description, '
    'amount, '
    'currency, '
    'value_date, '
    'counterparty_account, '
    'counterparty_name, '
    'communication_1, '
    'communication_2, '
    'operation_reference')

def to_qif(record):
    return """D{accounting_date}
T{amount}
N{operation_reference}
M{communication_1} {communication_2}
P{counterparty_name} ({counterparty_account})
^
""".format(**record)

with open('input.csv', 'rb') as csvfile:
    with open('out.qif', 'w') as outfile:
        outfile.write('!Type:Bank\n')
        acc_info = csvfile.readline()
        header = csvfile.readline()
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in csvreader:
            record = DataRow(*row)
            outfile.write(to_qif(record._asdict()))
