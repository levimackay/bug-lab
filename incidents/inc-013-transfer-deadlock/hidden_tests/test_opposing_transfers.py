from decimal import Decimal

from ledger.accounts import AccountBook
from ledger.audit import AuditLog
from ledger.transfers import Transfer, TransferService


def make(tmp_path):
    book = AccountBook()
    book.open("ACME", "5000.00")
    book.open("BOLT", "2200.00")
    return TransferService(book, AuditLog(tmp_path / "audit.db"))


def test_opposing_concurrent_transfers_complete(tmp_path):
    service = make(tmp_path)
    stuck = service.run_batch(
        [Transfer("a", "ACME", "BOLT", Decimal("1250.00")), Transfer("b", "BOLT", "ACME", Decimal("300.00"))],
        timeout=3.0,
    )
    assert stuck == [], f"transfers never finished: {stuck}"
    assert service.book.get("ACME").balance == Decimal("4050.00")
    assert service.book.get("BOLT").balance == Decimal("3150.00")
    assert service.audit.events("a") == ["started", "completed"]
    assert service.audit.events("b") == ["started", "completed"]


def test_total_is_conserved_under_contention(tmp_path):
    service = make(tmp_path)
    batch = [Transfer(f"x{i}", "ACME" if i % 2 else "BOLT", "BOLT" if i % 2 else "ACME", Decimal("10.00")) for i in range(4)]
    stuck = service.run_batch(batch, timeout=3.0)
    assert stuck == []
    assert service.book.total() == Decimal("7200.00")
