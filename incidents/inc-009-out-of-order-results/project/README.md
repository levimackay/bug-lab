# Order Enrichment Service

Takes a batch of orders off the queue and attaches the customer's loyalty
tier and shipping name to each one, by calling the Customer Directory
service once per order. Fulfillment will not pick up a batch until every
order in it has been enriched.

    node src/main.js     # run this morning's batch
    node --test           # run the test suite

`enrichOrders(orders)` returns `{ results, enriched, total }`. `results` is
the enriched order list, `enriched` is how many made it through, and `total`
is the batch size fulfillment expects to see accounted for.
