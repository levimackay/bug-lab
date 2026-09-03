import { ticketBus } from "./ticketBus.js";
import { waitForTicketUpdate } from "./waitForTicketUpdate.js";

const REQUEST_COUNT = 500;

async function main() {
  // A morning's worth of dashboard requests, each watching its own ticket.
  // Most tickets don't change while the agent has them open.
  const waits = [];
  for (let i = 0; i < REQUEST_COUNT; i++) {
    waits.push(waitForTicketUpdate(`tic-${i}`, 5));
  }
  const results = await Promise.all(waits);

  const timedOut = results.filter((r) => r.status === "timeout").length;
  const updated = results.length - timedOut;
  const leaked = ticketBus.listenerCount("ticket:update");

  console.log(`requests handled: ${results.length}`);
  console.log(`updated in time:  ${updated}`);
  console.log(`timed out:        ${timedOut}`);
  console.log(`listeners left on ticket:update: ${leaked}`);

  if (leaked > 0) {
    console.error(`ERROR: ${leaked} listeners still attached to ticketBus after every request finished`);
    process.exit(1);
  }
  process.exit(0);
}

main();
