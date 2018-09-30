import csv
import logging
from datetime import datetime
from decimal import Decimal

from ccp2qif.core import AccountInfo, QIFTransaction, TransactionList

LOG = logging.getLogger(__name__)


def sniff(file_pointer):
    LOG.debug('Trying to detect file-type using %s', __name__)
    file_pointer.seek(0)
    try:
        magic = file_pointer.read(6)
    except Exception as exc:
        LOG.debug('Unable to read from file (%s)!', exc)
        magic = None
    file_pointer.seek(0)
    if magic == 'BILnet':
        return parse
    return None


def parse(file_pointer, account_number=''):
    next(file_pointer)  # magic marker
    next(file_pointer)  # redundant heading
    raw_account_info = next(file_pointer).strip()
    account_number, _, description = raw_account_info.partition(' ')
    description = description.strip('\r\n\t "')
    account_info = AccountInfo(account_number, description)
    next(file_pointer)  # Empty line
    next(file_pointer)  # Column Names

    # Data starts now
    transactions = []
    reader = csv.reader(file_pointer, delimiter=';', quotechar='"')
    for line in reader:
        _, value_date, label, message, value, _ = line
        message = '%s | %s' % (label, message)
        date = datetime.strptime(value_date, '%d/%m/%Y').date()
        value = Decimal(value)
        transactions.append(QIFTransaction(date, value, message, '', ''))

    return TransactionList(account_info, transactions)
