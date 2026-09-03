import pytest

from inventory.store import InventoryStore, OutOfStock


@pytest.fixture
def store(tmp_path):
    s = InventoryStore(tmp_path / "ledger.db")
    s.set_stock("LAMP-9", 3)
    return s


def test_reserve_decrements_stock(store):
    rid = store.reserve("LAMP-9")
    assert len(rid) == 12
    assert store.stock("LAMP-9") == 2


def test_reserve_writes_ledger(store):
    store.reserve("LAMP-9", 2)
    assert [qty for _, qty in store.reservations("LAMP-9")] == [2]


def test_reserve_refuses_when_out_of_stock(store):
    store.reserve("LAMP-9", 3)
    with pytest.raises(OutOfStock):
        store.reserve("LAMP-9")
    assert store.stock("LAMP-9") == 0


def test_unknown_sku_has_no_stock(store):
    assert store.stock("NOPE") == 0
    with pytest.raises(OutOfStock):
        store.reserve("NOPE")
