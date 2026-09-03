# Ticket Live Updates

Support agents' dashboards long-poll for changes to a ticket they have open.
`waitForTicketUpdate(ticketId)` subscribes to the shared ticket bus and
resolves either when a matching update arrives or after a short timeout if
nothing changes.

    node src/main.js     # replay a morning's worth of dashboard watches
    node --test           # run the test suite

`ticketBus` is a plain `node:events` `EventEmitter` shared by every request.
A watch is meant to leave the bus exactly as it found it once it resolves,
whichever way it resolves.
