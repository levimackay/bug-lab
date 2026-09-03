from catalog.service import CatalogService


def test_get_price_returns_usd_price():
    service = CatalogService()
    price = service.get_price("SKU-TENT-2P", "USD")
    assert price.amount == 89.00
    assert price.currency == "USD"


def test_get_price_caches_repeat_lookups():
    service = CatalogService()
    first = service.get_price("SKU-STOVE-1B", "USD")
    second = service.get_price("SKU-STOVE-1B", "USD")
    assert first == second


def test_different_skus_have_different_prices():
    service = CatalogService()
    tent = service.get_price("SKU-TENT-2P", "USD")
    lantern = service.get_price("SKU-LANTERN", "USD")
    assert tent.amount != lantern.amount


def test_unknown_sku_raises():
    service = CatalogService()
    try:
        service.get_price("SKU-DOES-NOT-EXIST", "USD")
    except KeyError:
        return
    assert False, "expected KeyError for unknown sku"
