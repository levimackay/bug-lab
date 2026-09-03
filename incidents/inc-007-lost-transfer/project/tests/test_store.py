import pytest

from ledger.store import AccountFrozen, InsufficientFunds, LedgerStore


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(tmp_path / "ledger.db")
    s.open_account("A", "Alice", 10000)
    s.open_account("B", "Bob", 2000)
    return s


def test_transfer_moves_money_between_accounts(store):
    store.transfer("A", "B", 1500)
    assert store.balance("A") == 8500
    assert store.balance("B") == 3500


def test_transfer_refuses_when_source_has_insufficient_funds(store):
    with pytest.raises(InsufficientFunds):
        store.transfer("B", "A", 5000)
    assert store.balance("A") == 10000
    assert store.balance("B") == 2000


def test_multiple_transfers_accumulate_correctly(store):
    store.transfer("A", "B", 1000)
    store.transfer("A", "B", 500)
    assert store.balance("A") == 8500
    assert store.balance("B") == 3500


def test_unknown_account_raises_key_error(store):
    with pytest.raises(KeyError):
        store.transfer("A", "NOPE", 100)
