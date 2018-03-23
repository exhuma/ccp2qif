from collections import namedtuple


TransactionList = namedtuple('TransactionList', 'account transactions')
AccountInfo = namedtuple('AccountInfo', ['account_number', 'description'])
QIFTransaction = namedtuple(
    'QIFTransaction', [
        'date',
        'value',
        'message',
        'counterparty',
    ])
