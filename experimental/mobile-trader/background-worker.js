// FUT Trader 27 experimental collector. Deploy as a separate Cloudflare Worker.
// Required binding: FUT27_HISTORY (KV namespace). Cron trigger: */30 * * * *
// Data is unverified; never generate trading signals.
const SOURCE = 'https://fc27-market.val.run/latest';
const KEY = 'experimental-history-v1';
const GROUPS = ['icons','heroes','bronze','silver','gold','special'];
const HEADERS = {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Access-Control-Allow-Origin':'https://finaltradingfc.pages.dev','X-FUT27-Source-Status':'unverified'};
function snapshot(data) {
  if (!data || typeof data.updated !== 'string' || !data.groups || typeof data.groups !== 'object') throw Error('invalid_feed');
  const stamp = Date.parse(data.updated);
  if (!Number.isFinite(stamp) || Date.now()-stamp > 90*60000 || stamp-Date.now()>5*60000) throw Error('stale_feed');
  const cards=[],seen=new Set();
  for (const group of GROUPS) {
    const rows=data.groups[group]||[];
    if (!Array.isArray(rows)) throw Error('invalid_group');
    for (const r of rows) {
      if (!r || !Number.isSafeInteger(r.eaId) || r.eaId<=0 || !Number.isSafeInteger(r.price) || r.price<=0 || r.price>15000000 || typeof r.name!=='string' || !r.name.trim()) continue;
      const id=group+':'+r.eaId;
      if(seen.has(id)) throw Error('duplicate_card');
      seen.add(id);
      cards.push({group,ea_id:r.eaId,name:r.name.trim(),price:r.price,observed_at:data.updated});
    }
  }
  if(!cards.length) throw Error('empty_feed');
  return {schema:'fut27-experimental-feed-v1',source:SOURCE,verified:false,production_signals_enabled:false,updated_at:data.updated,cards};
}
async function collect(env) {
  if(!env.FUT27_HISTORY) throw Error('missing_kv_binding');
  const response=await fetch(SOURCE,{headers:{Accept:'application/json'},signal:AbortSignal.timeout(15000)});
  if(!response.ok) throw Error('upstream_http_'+response.status);
  const next=snapshot(await response.json());
  const old=await env.FUT27_HISTORY.get(KEY,'json');
  const snapshots=old&&Array.isArray(old.snapshots)?old.snapshots:[];
  const last=snapshots.at(-1);
  if(last && Date.parse(next.updated_at)<Date.parse(last.updated_at)) throw Error('timestamp_regressed');
  if(!last || last.updated_at!==next.updated_at) {
    snapshots.push(next);
    await env.FUT27_HISTORY.put(KEY,JSON.stringify({schema:'fut27-experimental-history-v1',snapshots:snapshots.slice(-336)}));
  }
  return {updated_at:next.updated_at,count:next.cards.length,stored:snapshots.length};
}
export default {
  async scheduled(event,env,ctx) {ctx.waitUntil(collect(env).catch(err=>console.error('experimental_collection_failed',String(err))));},
  async fetch(request,env) {
    const url=new URL(request.url);
    if(request.method!=='GET'||url.pathname!=='/history')return new Response('Not found',{status:404});
    if(!env.FUT27_HISTORY)return Response.json({error:'missing_kv_binding'},{status:503,headers:HEADERS});
    const data=await env.FUT27_HISTORY.get(KEY,'json');
    if(!data)return Response.json({error:'history_not_ready'},{status:503,headers:HEADERS});
    return new Response(JSON.stringify(data),{headers:HEADERS});
  }
};
