// Simulates the Customer Directory service: an internal lookup the
// enrichment job calls once per order to attach loyalty tier and a
// shipping name. In production this is an HTTP call to the accounts
// team's service; here it's an in-memory table with a network-shaped
// delay so timing bugs behave the same way they do against the real
// thing.

const CUSTOMERS = {
  cus_1001: { name: "Priya Natarajan", tier: "gold" },
  cus_1002: { name: "Owen Brasch", tier: "silver" },
  cus_1003: { name: "Marisol Vega", tier: "bronze" },
  cus_1004: { name: "Derek Holloway", tier: "gold" },
  cus_1005: { name: "Fatima Idris", tier: "silver" },
  cus_1006: { name: "Callum Reyes", tier: "bronze" },
};

// Different customer records answer at different speeds, the same way the
// real directory does under load. Deterministic so replays behave the same.
function delayFor(customerId) {
  let hash = 0;
  for (const ch of customerId) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return 5 + (hash % 40); // 5-44ms
}

export function lookupCustomer(customerId) {
  const record = CUSTOMERS[customerId];
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (!record) {
        reject(new Error(`unknown customer ${customerId}`));
        return;
      }
      resolve({ customerId, ...record });
    }, delayFor(customerId));
  });
}
