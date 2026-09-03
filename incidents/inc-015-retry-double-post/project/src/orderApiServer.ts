import http from "node:http";
import { randomUUID } from "node:crypto";

export interface OrderApiServer {
  url: string;
  orderCount: () => number;
  close: () => Promise<void>;
}

interface OrderRecord {
  orderId: string;
  customerId: string;
  sku: string;
  qty: number;
}

// A stand-in for the downstream Order API. Creates an order per POST unless
// it recognizes an Idempotency-Key it has already served, in which case it
// hands back the original order instead of creating a second one. The
// first request to arrive can be delayed past a typical client timeout,
// the same way the real Order API is under load, while every request after
// it answers immediately; the order is committed to the store the moment
// it's parsed, before that delay, not after.
export function startOrderApiServer(opts: { firstRequestDelayMs?: number } = {}): Promise<OrderApiServer> {
  const orders: OrderRecord[] = [];
  const byKey = new Map<string, OrderRecord>();
  let requestsSeen = 0;
  const firstRequestDelayMs = opts.firstRequestDelayMs ?? 0;

  const server = http.createServer((req, res) => {
    if (req.method !== "POST" || req.url !== "/orders") {
      res.writeHead(404).end();
      return;
    }
    const key = req.headers["idempotency-key"];
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      const requestNumber = ++requestsSeen;
      const parsed = JSON.parse(body);

      const existing = typeof key === "string" ? byKey.get(key) : undefined;
      const record: OrderRecord = existing ?? {
        orderId: randomUUID(),
        customerId: parsed.customerId,
        sku: parsed.sku,
        qty: parsed.qty,
      };
      if (!existing) {
        orders.push(record);
        if (typeof key === "string") byKey.set(key, record);
      }

      const respond = () => {
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ orderId: record.orderId }));
      };

      if (requestNumber === 1 && firstRequestDelayMs > 0) {
        setTimeout(respond, firstRequestDelayMs);
      } else {
        respond();
      }
    });
  });

  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        url: `http://127.0.0.1:${port}`,
        orderCount: () => orders.length,
        close: () => new Promise((r) => server.close(() => r())),
      });
    });
  });
}
