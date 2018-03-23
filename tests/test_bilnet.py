from datetime import date
from decimal import Decimal
from io import StringIO

from ccp2qif.bil import parse
from ccp2qif.core import (
    AccountInfo,
    QIFTransaction as QT,
    TransactionList,
    write_qif,
)


def test_parsing():
    expected = TransactionList(
        account=AccountInfo('LU123456789012345678',
                            'This is the account description'),
        transactions=[
            QT(date(2018, 3, 9), Decimal('-54.42'), 'label 1 | communication 1', ''),
            QT(date(2018, 3, 8), Decimal('-1000.00'), 'label 2 | communication 2', ''),
            QT(date(2018, 3, 5), Decimal('-56.00'), 'label 3 | communication 3', ''),
            QT(date(2018, 3, 5), Decimal('-16.00'), 'label 4 | communication 4', ''),
            QT(date(2018, 3, 5), Decimal('24.51'), 'label 5 | communication 5', ''),
            QT(date(2018, 3, 3), Decimal('-90.00'), 'label 6 | communication 6', ''),
            QT(date(2018, 1, 23), Decimal('-300.00'), 'label 7 | communication 7', ''),
        ]
    )
    with open('testdata/bil/liste_mouvements.txt') as infile:
        result = parse(infile)
    assert result.account == expected.account
    assert result.transactions == expected.transactions
    assert result == expected


def test_to_qif():
    with open('testdata/bil/liste_mouvements.txt') as infile:
        input_data = parse(infile)
    with open('testdata/bil/liste_mouvements.qif') as infile:
        expected = infile.read()
    output = StringIO()
    write_qif(input_data, output)
    result = output.getvalue()
    assert result == expected
