from __future__ import print_function
from collections import namedtuple
import codecs
import sys
from os.path import splitext

from ccp2qif.util import UnicodeReader

DataRow = namedtuple(
    'DataRow',
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


def convert(source_filename, target_filename, account_name=None):
    with open(source_filename, 'r') as csvfile:
        # if the filename is a valid IBAN number, we take this as account number
        base_name, _, _ = source_filename.rpartition('.')
        from schwifty import IBAN
        try:
            iban = IBAN(base_name)
        except ValueError:
            # not a valid IBAN number. We can ignore this.
            pass
        else:
            account_name = iban.compact
            print('Using %s as accound number (from filename): ' % account_name)

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
