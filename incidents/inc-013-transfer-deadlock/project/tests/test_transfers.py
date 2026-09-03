from decimal import Decimal

import pytest

from ledger.accounts import AccountBook, InsufficientFunds
from ledger.audit import AuditLog
from ledger.transfers import Transfer, TransferService


@pytest.fixture
def service(tmp_path):
    book = AccountBook()
    book.open("ACME", "500.00")
    book.open("BOLT", "100.00")
    book.open("CRUX", "50.00")
    return TransferService(book, AuditLog(tmp_path / "audit.db"))


def test_transfer_moves_money(service):
    service.transfer(Transfer("t1", "ACME", "BOLT", Decimal("120.00")))
    assert service.book.get("ACME").balance == Decimal("380.00")
    assert service.book.get("BOLT").balance == Decimal("220.00")


def test_transfer_is_audited(service):
    service.transfer(Transfer("t1", "ACME", "BOLT", Decimal("1.00")))
    assert service.audit.events("t1") == ["started", "completed"]


def test_insufficient_funds_declined(service):
    with pytest.raises(InsufficientFunds):
        service.transfer(Transfer("t2", "CRUX", "ACME", Decimal("60.00")))
    assert service.audit.events("t2") == ["declined"]
    assert service.book.total() == Decimal("650.00")


def test_opposing_transfers_in_sequence(service):
    service.transfer(Transfer("t3", "ACME", "BOLT", Decimal("10.00")))
    service.transfer(Transfer("t4", "BOLT", "ACME", Decimal("5.00")))
    assert service.book.get("ACME").balance == Decimal("495.00")


def test_batch_between_unrelated_accounts(service):
    stuck = service.run_batch([Transfer("t5", "ACME", "BOLT", Decimal("1.00")), Transfer("t6", "CRUX", "ACME", Decimal("1.00"))], timeout=5)
    assert stuck == []
    assert service.book.total() == Decimal("650.00")
