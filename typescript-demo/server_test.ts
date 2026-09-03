import { strict as assert } from "node:assert";
import { handler } from "./server.ts";

Deno.test("GET / returns the counter page", async () => {
  const res = await handler(new Request("http://localhost/"));
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("content-type"), "text/html; charset=utf-8");
  const body = await res.text();
  assert.ok(body.includes("カウンターデモ (TypeScript版)"));
});

Deno.test("GET /style.css returns CSS", async () => {
  const res = await handler(new Request("http://localhost/style.css"));
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("content-type"), "text/css; charset=utf-8");
});

Deno.test("GET /unknown returns 404", async () => {
  const res = await handler(new Request("http://localhost/unknown"));
  assert.equal(res.status, 404);
});
