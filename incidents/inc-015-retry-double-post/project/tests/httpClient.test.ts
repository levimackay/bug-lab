import { test } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { postJson, TimeoutError } from "../src/httpClient.ts";

function startEchoServer(): Promise<{ url: string; close: () => Promise<void> }> {
  const server = http.createServer((req, res) => {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(body || "{}");
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({ url: `http://127.0.0.1:${port}`, close: () => new Promise((r) => server.close(() => r())) });
    });
  });
}

test("postJson resolves with the parsed response body", async () => {
  const server = await startEchoServer();
  try {
    const result = await postJson<{ ping: string }>(`${server.url}/`, { ping: "pong" }, { timeoutMs: 1000 });
    assert.equal(result.ping, "pong");
  } finally {
    await server.close();
  }
});

test("postJson raises TimeoutError when the peer never responds", async () => {
  const server = http.createServer(() => {
    /* never respond */
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  const port = typeof address === "object" && address ? address.port : 0;
  try {
    await assert.rejects(() => postJson(`http://127.0.0.1:${port}/`, {}, { timeoutMs: 30 }), TimeoutError);
  } finally {
    server.close();
  }
});
