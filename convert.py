import csv
from collections import namedtuple
import codecs

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
    return u"""D{accounting_date}
T{amount}
N{operation_reference}
M{communication_1} {communication_2}
P{counterparty_name} ({counterparty_account})
^
""".format(**record)


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


def convert(source_filename, target_filename):
    with open(source_filename, 'r') as csvfile:
        with codecs.open(target_filename, 'w', encoding='utf8') as outfile:
            outfile.write(u'!Type:Bank\n')
            acc_info = csvfile.readline()
            header = csvfile.readline()
            csvreader = UnicodeReader(csvfile, delimiter=';', quotechar='"',
                encoding='latin1')
            for row in csvreader:
                record = DataRow(*row)
                outfile.write(to_qif(record._asdict()))
                print u'Wrote {0.accounting_date} - {0.communication_1}'.format(
                        record).encode('utf8')


if __name__ == "__main__":
    convert('input.csv', 'out.qif')
