// Cloudflare Pages Function. Experimental third-party feed, NOT verified market data.
const UPSTREAM = 'https://fc27-market.val.run/latest';
export async function onRequestGet() {
  try {
    const response = await fetch(UPSTREAM, {
      headers: { Accept: 'application/json', 'User-Agent': 'FUT-Trader-27-experimental/1.0' },
      redirect: 'follow',
      signal: AbortSignal.timeout(12000),
    });
    if (!response.ok) return Response.json({ error: 'upstream_unavailable' }, { status: 502, headers: { 'Cache-Control': 'no-store' } });
    const data = await response.json();
    if (!data || typeof data !== 'object' || typeof data.updated !== 'string' || !data.groups || typeof data.groups !== 'object')
      return Response.json({ error: 'invalid_upstream' }, { status: 502, headers: { 'Cache-Control': 'no-store' } });
    return Response.json(data, { headers: { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex', 'X-FUT27-Source-Status': 'unverified' } });
  } catch (error) {
    const kind = error && error.name === 'TimeoutError' ? 'upstream_timeout' : error && error.name === 'SyntaxError' ? 'invalid_json' : 'upstream_connection_failed';
    return Response.json({ error: kind, hint: 'Cloudflare could not retrieve the experimental upstream feed' }, { status: 502, headers: { 'Cache-Control': 'no-store' } });
  }
}
