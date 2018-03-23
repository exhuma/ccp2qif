from __future__ import print_function
from collections import namedtuple
from functools import partial
from os.path import splitext
from typing import TextIO
import codecs
import sys

from schwifty import IBAN

from ccp2qif.util import UnicodeReader
from ccp2qif.ccp import (
    try_getting_account_number,
    convert_csv,
    convert_excel,
)

TransactionList = namedtuple('TransactionList', 'account transactions')
AccountInfo = namedtuple('AccountInfo', ['account_number', 'description'])

QIFTransaction = namedtuple(
    'QIFTransaction', [
        'date',
        'value',
        'message'
    ])


def write_qif(transaction_list: TransactionList, outfile: TextIO,
              datefmt: str = '%d/%m/%Y'):
    '''
    Converts a transaction list to a QIF file
    '''
    write = partial(print, file=outfile)
    write('!Type:Bank')
    write('!Account')
    write('N%s' % transaction_list.account.account_number)
    write('D"%s"' % transaction_list.account.description)
    write('^')
    for transaction in transaction_list.transactions:
        write('D%s' % transaction.date.strftime(datefmt))
        write('T%s' % transaction.value)
        write('M%s' % transaction.message)
        write('^')


def convert(source_filename, target_filename, account_name=None):
    _, _, extension = source_filename.lower().rpartition('.')
    if extension == 'xls':
        func = convert_excel
    elif extension == 'csv':
        func = convert_csv
    else:
        raise ValueError('Unsupported file format: %r' % extension)
    func(source_filename, target_filename, account_name)


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
