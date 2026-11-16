'use strict';
const file=document.getElementById('file'),statusEl=document.getElementById('status'),root=document.getElementById('results'),filter=document.getElementById('filter');
let report=null;
const node=(tag,text)=>{const e=document.createElement(tag);e.textContent=String(text);return e};
const number=n=>Number.isFinite(n)?n.toLocaleString('it-IT'):'n.d.';
function render(){
  root.replaceChildren();
  if(!report)return;
  const candidates=new Set(report.candidates.map(r=>r.id));
  for(const r of report.rows){
    if(filter.value==='candidates'&&!candidates.has(r.id))continue;
    const a=node('article','');
    a.append(node('h2',r.name+' — SINTETICA'),node('p','ID di test: '+r.id+' · Fonte: '+r.source_id));
    a.append(node('p','Prezzo sintetico: '+number(r.price)+' · Età al calcolo: '+number(r.age_seconds)+' s'));
    const at=Date.parse(r.timestamp),age=Date.now()-at;
    if(!Number.isFinite(at)||age<0||age>3600000)a.append(node('p','Attenzione: data futura, mancante o quotazione vecchia rispetto a ora.'));
    a.append(node('p',['1h','6h','24h'].map(k=>k+': '+(r.changes_percent?.[k]==null?'n.d.':number(r.changes_percent[k])+'%')).join(' · ')));
    a.append(node('p','Target storico sintetico: '+number(r.sell_target_estimate)+' · Margine netto stimato: '+number(r.net_profit_estimate)+' · ROI: '+number(r.net_roi_percent)+'%'));
    const risk=node('p','Rischio: '+number(r.risk?.score)+'/100 · '+r.risk?.level);risk.className='risk';a.append(risk);
    a.append(node('p','Indicatori: '+r.risk_flags.join(', ')),node('small',r.warning));root.append(a);
  }
}
file.addEventListener('change',async()=>{
  report=null;root.replaceChildren();
  try{
    const f=file.files[0];if(!f)return;if(f.size>2000000)throw Error('Massimo 2 MB');
    const data=JSON.parse(await f.text());
    if(data.engine!=='experimental-scanner-v1'||data.data_kind!=='synthetic'||data.simulated!==true||data.authorized!==false||!Array.isArray(data.production_signals)||data.production_signals.length||!Array.isArray(data.rows)||!Array.isArray(data.candidates)||data.rows.length>1000||data.candidates.length>1000)throw Error('Accettati solo report sintetici offline, senza segnali operativi');
    if(data.rows.some(r=>r.simulated!==true||r.actionable!==false||!Array.isArray(r.risk_flags)))throw Error('Etichette sintetiche mancanti');
    report=data;statusEl.textContent=data.rows.length+' carte sintetiche · '+data.candidates.length+' candidate di test · 0 segnali reali';render();
  }catch(e){report=null;root.replaceChildren();statusEl.textContent='Errore: '+e.message;}
});
filter.addEventListener('change',render);
document.getElementById('clear').onclick=()=>{report=null;file.value='';root.replaceChildren();statusEl.textContent='Nessun report caricato.'};
