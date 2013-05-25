from __future__ import print_function
import csv
from collections import namedtuple
import codecs
import sys
from os.path import splitext

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


def convert(source_filename, target_filename, account_name=None):
    with open(source_filename, 'r') as csvfile:
        with codecs.open(target_filename, 'w', encoding='utf8') as outfile:
            if account_name:
                outfile.write('!Account\n')
                outfile.write('N{0}\n'.format(account_name))
                outfile.write('TBank\n')
                outfile.write('^\n')
            outfile.write(u'!Type:Bank\n')
            acc_info = csvfile.readline()
            header = csvfile.readline()
            csvreader = UnicodeReader(csvfile, delimiter=';', quotechar='"',
                encoding='latin1')
            for row in csvreader:
                record = DataRow(*row)
                outfile.write(to_qif(record._asdict()))
                print(u'Wrote {0.accounting_date} - {0.communication_1}'.format(
                    record).encode('utf8'))



def climain():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] <infile>")
    parser.add_option('-n', '--account-name', dest='account_name',
                      help='The name of the account for this import',
                      default=None)
    parser.add_option('-o', '--outfile', dest='outfile',
                      help='The output file.', default=None)
    (options, args) = parser.parse_args()

    if not args:
        print('Requirement argument <infile> not specified!',
              file=sys.stderr)
        parser.print_usage(sys.stderr)
        return 9

    infile = args[0]
    if options.outfile:
        outfile = options.outfile
    else:
        base, ext = splitext(infile)
        if ext.lower() == 'qif':
            print('Error: The input file seems to be a qif file already!',
                  file=sys.stderr)
            return 9
        outfile = '{0}.qif'.format(base)


    convert(infile,
            outfile,
            account_name=options.account_name)



if __name__ == "__main__":
    climain()
