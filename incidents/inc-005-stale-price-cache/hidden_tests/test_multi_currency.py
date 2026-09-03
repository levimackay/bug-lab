from catalog.service import CatalogService


def test_second_currency_is_not_served_from_first_currencys_cache_entry():
    service = CatalogService()
    usd = service.get_price("SKU-TENT-2P", "USD")
    eur = service.get_price("SKU-TENT-2P", "EUR")

    assert usd.currency == "USD"
    assert eur.currency == "EUR"
    assert eur.amount == 82.50
    assert usd.amount != eur.amount


def test_three_currencies_each_cache_independently():
    service = CatalogService()
    prices = {c: service.get_price("SKU-STOVE-1B", c) for c in ("USD", "EUR", "GBP")}
    for currency, price in prices.items():
        assert price.currency == currency

    # repeat lookups still hit the cache and stay correct per currency
    for currency, price in prices.items():
        assert service.get_price("SKU-STOVE-1B", currency) == price
