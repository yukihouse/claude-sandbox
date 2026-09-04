const PORT = 5004;

const contentTypes: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

async function serveStatic(path: string): Promise<Response> {
  const ext = path.slice(path.lastIndexOf("."));
  const contentType = contentTypes[ext] ?? "application/octet-stream";

  try {
    const data = await Deno.readFile(path);
    return new Response(data, { headers: { "content-type": contentType } });
  } catch {
    return new Response("Not Found", { status: 404 });
  }
}

// 複数タブ・複数ブラウザでカウンターをリアルタイムに同期する
// 「👥 みんなで見てるカウンター」機能のための共有状態。
let sharedCount = 0;
const clients = new Set<WebSocket>();

type ClientMessage = { type: "increment" } | { type: "reset" };

function broadcastState(): void {
  const payload = JSON.stringify({ count: sharedCount, viewers: clients.size });
  for (const socket of clients) {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(payload);
    }
  }
}

function handleWebSocket(req: Request): Response {
  const { socket, response } = Deno.upgradeWebSocket(req);

  socket.onopen = () => {
    clients.add(socket);
    broadcastState();
  };

  socket.onmessage = (event) => {
    const message = JSON.parse(event.data as string) as ClientMessage;

    if (message.type === "increment") {
      sharedCount += 1;
    } else if (message.type === "reset") {
      sharedCount = 0;
    }

    broadcastState();
  };

  socket.onclose = () => {
    clients.delete(socket);
    broadcastState();
  };

  return response;
}

export function handler(req: Request): Promise<Response> {
  const { pathname } = new URL(req.url);

  if (pathname === "/ws") {
    return Promise.resolve(handleWebSocket(req));
  }

  if (pathname === "/" || pathname === "/index.html") {
    return serveStatic("./static/index.html");
  }

  if (pathname === "/style.css") {
    return serveStatic("./static/style.css");
  }

  return Promise.resolve(new Response("Not Found", { status: 404 }));
}

if (import.meta.main) {
  Deno.serve({ port: PORT }, handler);
  console.log(`Listening on http://localhost:${PORT}`);
}
