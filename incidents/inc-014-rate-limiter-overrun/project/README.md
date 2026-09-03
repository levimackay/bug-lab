# Payments Gateway Client

Wraps the third-party payments API. The API disconnects any client that
sends more than a fixed number of requests in a billing window, so every
outbound charge goes through a shared token-bucket `RateLimiter` first.

    node src/main.ts     # replay a retry-storm burst of charges
    node --test           # run the test suite

`RateLimiter.acquire()` resolves `true` if the caller may spend a token,
`false` if the window's budget is exhausted. `PaymentsApiClient.charge(orderId)`
calls it before sending a charge and reports `"charged"` or `"throttled"`.
