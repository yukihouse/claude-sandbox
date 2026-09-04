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

Deno.test("WebSocket clients receive synced state", async () => {
  const server = Deno.serve({ port: 0, onListen: () => {} }, handler);
  const { port } = server.addr as Deno.NetAddr;

  function nextMessage(socket: WebSocket): Promise<{ count: number; viewers: number }> {
    return new Promise((resolve) => {
      socket.addEventListener(
        "message",
        (event) => resolve(JSON.parse(event.data as string)),
        { once: true },
      );
    });
  }

  const socketA = new WebSocket(`ws://localhost:${port}/ws`);
  await new Promise((resolve) => socketA.addEventListener("open", resolve, { once: true }));

  const initial = await nextMessage(socketA);
  assert.equal(initial.count, 0);
  assert.equal(initial.viewers, 1);

  const afterConnect = nextMessage(socketA);
  const socketB = new WebSocket(`ws://localhost:${port}/ws`);
  await new Promise((resolve) => socketB.addEventListener("open", resolve, { once: true }));
  assert.equal((await afterConnect).viewers, 2);

  const afterIncrement = nextMessage(socketA);
  socketB.send(JSON.stringify({ type: "increment" }));
  assert.equal((await afterIncrement).count, 1);

  const afterReset = nextMessage(socketA);
  socketB.send(JSON.stringify({ type: "reset" }));
  assert.equal((await afterReset).count, 0);

  socketA.close();
  socketB.close();
  await server.shutdown();
});
