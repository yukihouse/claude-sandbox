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

export function handler(req: Request): Promise<Response> {
  const { pathname } = new URL(req.url);

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
