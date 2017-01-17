from __future__ import print_function
from collections import namedtuple
import codecs
import sys
from os.path import splitext, basename

from schwifty import IBAN

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


def clean_join(record, fields):
    """
    Join only fields which have a value
    """
    return '; '.join([record[_] for _ in fields if record[_].strip()])


def to_qif(record):
    message = clean_join(record,
                         ('communication_1', 'communication_2', 'description'))
    counterparty = clean_join(record,
                              ('counterparty_name', 'counterparty_account'))

    return u"""D{accounting_date}
T{amount}
N{operation_reference}
M{message_}
P{counterparty_}
^
""".format(message_=message, counterparty_=counterparty, **record)


def account_name_from_filename(filename):
    # if the filename is a valid IBAN number, we take this as account number
    base_name, _, _ = basename(filename).rpartition('.')
    try:
        iban = IBAN(base_name)
    except ValueError:
        # not a valid IBAN number. We can ignore this.
        return None
    else:
        return iban.formatted


def try_getting_account_number(line):
    if line.lower().startswith('account number'):
        account_info = line.split(';')
        raw_account_number = account_info[1]
        try:
            account_number = IBAN(raw_account_number)
        except ValueError:
            return None
        else:
            return account_number.formatted
    else:
        return None


def convert(source_filename, target_filename, account_name=None):
    detected_account_name = account_name_from_filename(source_filename)
    if not account_name and detected_account_name:
        print('Using %s as account number (from filename): ' %
              detected_account_name)
        account_name = detected_account_name
    elif account_name:
        print('Using %s as account number (from CLI argument): ' %
              account_name)
    else:
        print('No account number manually specified')

    with open(source_filename, 'r') as csvfile:
        with codecs.open(target_filename, 'w', encoding='utf8') as outfile:

            # If the file contains a line with account info, this overrides the
            # rest.
            account_line = csvfile.readline()
            account_number = try_getting_account_number(account_line)
            if account_number:
                print('Account number %r found in file. Overriding manual '
                      'value' % account_number)
                account_name = account_number

            if account_name:
                outfile.write('!Account\n')
                outfile.write('N{0}\n'.format(account_name))
                outfile.write('TBank\n')
                outfile.write('^\n')
            outfile.write(u'!Type:Bank\n')

            csvfile.readline()  # skip header
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
