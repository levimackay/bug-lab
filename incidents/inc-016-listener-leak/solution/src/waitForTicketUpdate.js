import { ticketBus } from "./ticketBus.js";

// Waits for the next update to a specific ticket, or gives up after
// `timeoutMs` and reports that nothing changed yet. The support dashboard
// calls this once per ticket it's watching and blocks the request on it,
// long-poll style.
export function waitForTicketUpdate(ticketId, timeoutMs = 50) {
  return new Promise((resolve) => {
    function onUpdate(update) {
      if (update.ticketId !== ticketId) return;
      cleanup();
      resolve({ status: "updated", update });
    }

    function cleanup() {
      ticketBus.off("ticket:update", onUpdate);
      clearTimeout(timer);
    }

    const timer = setTimeout(() => {
      cleanup();
      resolve({ status: "timeout" });
    }, timeoutMs);

    ticketBus.on("ticket:update", onUpdate);
  });
}
