'use strict';
const file=document.getElementById('file'),statusEl=document.getElementById('status'),root=document.getElementById('results'),filter=document.getElementById('filter'),sort=document.getElementById('sort');
let report=null;
const node=(tag,text,cls)=>{const e=document.createElement(tag);e.textContent=String(text);if(cls)e.className=cls;return e};
const number=n=>typeof n==='number'&&Number.isFinite(n)?n.toLocaleString('it-IT'):'n.d.';
const signed=n=>typeof n==='number'&&Number.isFinite(n)?(n>0?'+':'')+number(n):'n.d.';
const riskName={low:'Basso',medium:'Medio',high:'Alto'};
const flagName={synthetic_test_data:'Dato sintetico',stale_quote:'Prezzo vecchio nel test',liquidity_unknown:'Liquidità non disponibile',low_liquidity:'Liquidità bassa',missing_windows:'Storico incompleto',anomalous_history:'Storico anomalo',volatile_history:'Prezzo volatile',insufficient_history:'Storico insufficiente',future_quote:'Data futura',invalid_history:'Storico non valido'};
function render(){
  root.replaceChildren();
  if(!report)return;
  const candidates=new Set(report.candidates.map(r=>r.id));
  const rows=report.rows.filter(r=>filter.value!=='candidates'||candidates.has(r.id));
  const val=(r,k)=>Number.isFinite(r[k])?r[k]:-Infinity;
  rows.sort((a,b)=>sort.value==='risk'?(val(a.risk||{},'score')-val(b.risk||{},'score')):sort.value==='name'?String(a.name).localeCompare(String(b.name),'it'):val(b,sort.value==='roi'?'net_roi_percent':'net_profit_estimate')-val(a,sort.value==='roi'?'net_roi_percent':'net_profit_estimate'));
  if(!rows.length){root.append(node('p','Nessuna carta di test per il filtro selezionato.','empty'));return;}
  for(const r of rows){
    const card=node('article','');const top=node('div','','card-top'),title=node('div','');
    title.append(node('h2',r.name+' — SINTETICA'),node('small','ID '+r.id+' · '+(r.version||'TEST')));
    top.append(title,node('span',candidates.has(r.id)?'Candidata demo':'Solo analisi','pill'+(candidates.has(r.id)?' good':'')));card.append(top);
    const prices=node('div','','price-grid');
    for(const [label,value] of [['Prezzo di test',r.price],['Target ipotetico',r.sell_target_estimate]]){const item=node('div','');item.append(node('span',label),node('strong',number(value)));prices.append(item)}
    card.append(prices);
    const profit=node('div','','profit');profit.append(node('span','Profitto netto ipotetico · commissione EA 5%'),node('strong',signed(r.net_profit_estimate)+' crediti'),node('small','ROI stimato: '+signed(r.net_roi_percent)+'%'));card.append(profit);
    const trends=node('div','','trends');
    for(const k of ['1h','6h','24h'])trends.append(node('span',k+'  '+signed(r.changes_percent?.[k])+'%','trend'));
    card.append(trends);
    const risk=node('div','','riskline');risk.append(node('span','Rischio indicativo'),node('strong',number(r.risk?.score)+'/100 · '+(riskName[r.risk?.level]||'n.d.')));card.append(risk);
    const meter=node('div','','meter'),fill=node('i','');fill.style.width=Math.max(0,Math.min(100,Number(r.risk?.score)||0))+'%';meter.append(fill);card.append(meter);
    const details=node('details','','details');details.append(node('summary','Dettagli e limiti'));
    details.append(node('p','Fonte: '+r.source_id+' · Data: '+(r.source_id==='synthetic-static-demo'?'fissa, solo per la demo':r.timestamp||'n.d.')));
    details.append(node('p','Indicatori: '+(r.risk_flags||[]).map(f=>flagName[f]||f).join(', ')));
    details.append(node('p',r.warning||'Nessun dato di mercato verificato.'));
    card.append(details);root.append(card);
  }
}
function accept(data){
  if(data.engine!=='experimental-scanner-v1'||data.data_kind!=='synthetic'||data.simulated!==true||data.authorized!==false||!Array.isArray(data.production_signals)||data.production_signals.length||!Array.isArray(data.rows)||!Array.isArray(data.candidates)||data.rows.length>1000||data.candidates.length>1000)throw Error('Accettati solo report sintetici offline, senza segnali operativi');
  if(data.rows.some(r=>r.simulated!==true||r.actionable!==false||!Array.isArray(r.risk_flags)))throw Error('Etichette sintetiche mancanti');
  report=data;document.getElementById('count').textContent=data.rows.length;document.getElementById('candidate-count').textContent=data.candidates.length;
  statusEl.textContent=data.rows.length+' carte sintetiche · '+data.candidates.length+' candidate di test · 0 segnali reali';render();
}
function clear(){
  report=null;file.value='';root.replaceChildren();document.getElementById('count').textContent='—';document.getElementById('candidate-count').textContent='—';statusEl.textContent='Nessun report caricato.';
}
file.addEventListener('change',async()=>{
  clear();
  try{const f=file.files[0];if(!f)return;if(f.size>2000000)throw Error('Massimo 2 MB');accept(JSON.parse(await f.text()));}
  catch(e){clear();statusEl.textContent='Errore: '+e.message;}
});
filter.addEventListener('change',render);sort.addEventListener('change',render);
document.getElementById('clear').onclick=clear;
async function loadStaticDemo(){
  if(location.protocol==='file:'){statusEl.textContent='Per il caricamento automatico apri la demo tramite un server web.';return;}
  try{const response=await fetch('./demo-data.json',{cache:'no-store'});if(!response.ok)throw Error('Demo non disponibile');accept(await response.json());}
  catch(e){if(!report)statusEl.textContent='Demo automatica non disponibile: '+e.message;}
}
document.getElementById('reload').onclick=()=>{clear();loadStaticDemo()};
loadStaticDemo();
