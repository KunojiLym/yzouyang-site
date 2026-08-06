/**
 * Cloudflare Worker collector for DIY pageviews.
 * Deploy: cd collect && npx wrangler deploy
 * Bind optional Analytics Engine dataset `EVENTS` for queryable aggregates.
 */
const MAX_BYTES = 4096;

function corsHeaders(origin, allowed) {
  const headers = {
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Max-Age": "86400",
    "Cache-Control": "no-store",
  };
  if (origin && (allowed.includes("*") || allowed.includes(origin))) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers["Vary"] = "Origin";
  }
  return headers;
}

function cleanEvent(event) {
  return {
    t: "pageview",
    v: Number(event.v || 1),
    ts: String(event.ts || new Date().toISOString()).slice(0, 40),
    path: String(event.path || "").slice(0, 512),
    host: String(event.host || "").slice(0, 253),
    title: String(event.title || "").slice(0, 256),
    ref: String(event.ref || "").slice(0, 253),
    lang: String(event.lang || "").slice(0, 16),
    tz: String(event.tz || "").slice(0, 64),
    vw: Number(event.vw || 0),
    vh: Number(event.vh || 0),
  };
}

export default {
  async fetch(request, env) {
    const allowed = (env.ALLOWED_ORIGINS || "*")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const origin = request.headers.get("Origin");
    const cors = corsHeaders(origin, allowed);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname.replace(/\/$/, "") !== "/collect") {
      return new Response("not found", { status: 404, headers: cors });
    }

    const bytes = await request.arrayBuffer();
    if (bytes.byteLength <= 0 || bytes.byteLength > MAX_BYTES) {
      return new Response(null, {
        status: bytes.byteLength > MAX_BYTES ? 413 : 400,
        headers: cors,
      });
    }

    let event;
    try {
      event = JSON.parse(new TextDecoder("utf-8").decode(bytes));
    } catch {
      return new Response(null, { status: 400, headers: cors });
    }
    if (!event || event.t !== "pageview") {
      return new Response(null, { status: 400, headers: cors });
    }

    const clean = cleanEvent(event);

    if (env.EVENTS && typeof env.EVENTS.writeDataPoint === "function") {
      env.EVENTS.writeDataPoint({
        blobs: [clean.host, clean.path, clean.ref, clean.tz, clean.lang],
        doubles: [clean.vw, clean.vh],
        indexes: [clean.host],
      });
    }

    if (env.EVENTS_BUCKET) {
      const day = clean.ts.slice(0, 10) || new Date().toISOString().slice(0, 10);
      const key = `diy/${day}/${crypto.randomUUID()}.json`;
      await env.EVENTS_BUCKET.put(key, JSON.stringify(clean), {
        httpMetadata: { contentType: "application/json" },
      });
    }

    return new Response(null, { status: 204, headers: cors });
  },
};
