import pytest

from ledger.report import total_balance
from ledger.store import AccountFrozen, LedgerStore


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(tmp_path / "ledger.db")
    s.open_account("CHECK", "Checking", 10000)
    s.open_account("SAVE", "Savings", 5000)
    s.freeze("SAVE")
    return s


def test_transfer_to_frozen_account_raises(store):
    with pytest.raises(AccountFrozen):
        store.transfer("CHECK", "SAVE", 2500)


def test_source_balance_is_unchanged_when_destination_is_frozen(store):
    with pytest.raises(AccountFrozen):
        store.transfer("CHECK", "SAVE", 2500)
    assert store.balance("CHECK") == 10000


def test_total_balance_is_conserved_when_transfer_is_blocked(store):
    before = total_balance(store, ["CHECK", "SAVE"])
    with pytest.raises(AccountFrozen):
        store.transfer("CHECK", "SAVE", 2500)
    after = total_balance(store, ["CHECK", "SAVE"])
    assert after == before
