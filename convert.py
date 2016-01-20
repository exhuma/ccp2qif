from __future__ import print_function
import xlrd
import codecs
from collections import namedtuple
import sys
from os.path import splitext
from datetime import datetime

CCardRow = namedtuple('CCardRow',
    'accounting_date, '
    'operation_date, '
    'card_number, '
    'description, '
    'original_amount, '
    'amount'
)

DataRow = namedtuple('DataRow',
    'accounting_date, '
    'description, '
    'counterparty_account, '
    'counterparty_name, '
    'amount'
)

def to_qif(record):
    return u"""D{0.accounting_date}
T{0.amount}
P{0.description}
^
""".format(record)


def date_converter(book):
    def fun(date):
        date_tuple = xlrd.xldate_as_tuple(date.value, book.datemode)
        return datetime(*date_tuple)
    return fun


def convert(source_filename, target_filename, account_name=None):
    workbook = xlrd.open_workbook(source_filename)
    convert_date = date_converter(workbook)
    sheet = workbook.sheet_by_index(0)
    with codecs.open(target_filename, 'w', encoding='utf8') as outfile:
        if account_name:
            outfile.write('!Account\n')
            outfile.write('N{0}\n'.format(account_name))
            outfile.write('TBank\n')
            outfile.write('^\n')
        outfile.write(u'!Type:Bank\n')

        for ridx in range(sheet.nrows):
            if ridx == 0:
                continue  # Skip header
            xlrow = sheet.row(ridx)
            row = CCardRow(
                convert_date(xlrow[0]),
                convert_date(xlrow[1]),
                xlrow[2].value,
                xlrow[3].value,
                xlrow[4].value,
                xlrow[5].value,
            )
            outfile.write(to_qif(row))


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
