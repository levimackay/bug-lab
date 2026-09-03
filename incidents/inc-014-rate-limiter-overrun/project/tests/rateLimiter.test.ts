import { test } from "node:test";
import assert from "node:assert/strict";
import { RateLimiter } from "../src/rateLimiter.ts";

test("acquire succeeds while tokens remain, called one at a time", async () => {
  const limiter = new RateLimiter("test-client", 3);
  assert.equal(await limiter.acquire(), true);
  assert.equal(await limiter.acquire(), true);
  assert.equal(await limiter.acquire(), true);
  assert.equal(limiter.remaining, 0);
});

test("acquire refuses once the bucket is empty", async () => {
  const limiter = new RateLimiter("test-client", 1);
  assert.equal(await limiter.acquire(), true);
  assert.equal(await limiter.acquire(), false);
  assert.equal(await limiter.acquire(), false);
});

test("resetWindow restores the full capacity", async () => {
  const limiter = new RateLimiter("test-client", 2);
  await limiter.acquire();
  await limiter.acquire();
  assert.equal(limiter.remaining, 0);
  limiter.resetWindow();
  assert.equal(limiter.remaining, 2);
  assert.equal(await limiter.acquire(), true);
});
