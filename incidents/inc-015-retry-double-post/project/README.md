# Order API Client

Creates orders against the downstream Order API. That API is occasionally
slow enough to blow past a normal client timeout even when the create
already succeeded on its end, so the client retries once on timeout rather
than treating every timeout as a failure.

    node src/main.ts     # reproduce a slow-but-successful create
    node --test           # run the test suite

`createOrder(baseUrl, order)` posts to `${baseUrl}/orders` and retries once
if the first attempt times out. `startOrderApiServer()` is a local stand-in
for the Order API, used here and in the tests; it dedupes by
`Idempotency-Key` when one is present and otherwise creates a new order per
request.
