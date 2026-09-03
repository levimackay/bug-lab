from inventory.service import ReservationService
from inventory.store import InventoryStore


def test_burst_never_oversells(tmp_path):
    store = InventoryStore(tmp_path / "ledger.db")
    store.set_stock("LAMP-9", 20)
    outcomes = ReservationService(store).burst([f"b{i}" for i in range(37)], "LAMP-9")
    accepted = sum(1 for o in outcomes if o.reservation_id)
    assert accepted == 20
    assert store.stock("LAMP-9") == 0
    assert len(store.reservations("LAMP-9")) == 20


def test_invariant_holds_with_multi_unit_orders(tmp_path):
    store = InventoryStore(tmp_path / "ledger.db")
    store.set_stock("LAMP-9", 10)
    outcomes = ReservationService(store).burst([f"b{i}" for i in range(24)], "LAMP-9", qty=2)
    accepted = sum(1 for o in outcomes if o.reservation_id)
    assert accepted * 2 + store.stock("LAMP-9") == 10
    assert accepted == 5
