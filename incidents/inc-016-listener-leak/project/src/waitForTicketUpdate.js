import { ticketBus } from "./ticketBus.js";

// Waits for the next update to a specific ticket, or gives up after
// `timeoutMs` and reports that nothing changed yet. The support dashboard
// calls this once per ticket it's watching and blocks the request on it,
// long-poll style.
export function waitForTicketUpdate(ticketId, timeoutMs = 50) {
  return new Promise((resolve) => {
    function onUpdate(update) {
      if (update.ticketId !== ticketId) return;
      ticketBus.off("ticket:update", onUpdate);
      resolve({ status: "updated", update });
    }

    ticketBus.on("ticket:update", onUpdate);

    setTimeout(() => {
      resolve({ status: "timeout" });
    }, timeoutMs);
  });
}
