'use strict';const el=id=>document.getElementById(id);let pageUrl='';el('read').onclick=async()=>{try{const [tab]=await chrome.tabs.query({active:true,currentWindow:true});if(!tab||!tab.url||!tab.url.startsWith('https://'))throw Error('Apri una pagina https');pageUrl=tab.url;const results=await chrome.scripting.executeScript({target:{tabId:tab.id},func:()=>window.getSelection()?.toString().trim().slice(0,160)||''});const selected=results[0]?.result||'';el('selected').textContent=selected||'Nessun testo selezionato';const candidate=selected.replace(/[^0-9]/g,'');if(candidate&&candidate.length<=8)el('buy').value=candidate;el('status').textContent='Verifica manualmente ID, prezzo e riferimento prima di esportare.'}catch(e){el('status').textContent=e.message}};el('export').onclick=()=>{const id=el('id').value.trim(),name=el('name').value.trim(),buy=Number(el('buy').value),target=Number(el('target').value);if(!/^[1-9][0-9]*$/.test(id)||!name||name.length>80||!Number.isSafeInteger(buy)||!Number.isSafeInteger(target)||buy<1||target<1||buy>15000000||target>15000000||!pageUrl){el('status').textContent='Prima leggi una selezione e completa i campi validi.';return}const record={id,name,strategy:el('strategy').value,buy,target,history:1,source:pageUrl,observed:new Date().toISOString()};const data={format:'fut-trader-27-observations-v1',data_kind:'manual_unverified',production_signals:[],records:[record]};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='fut-trader-27-capture.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);el('status').textContent='File creato. Importalo nel Trading Desk.'};
let detectedListings=[];
el('scan').onclick=async()=>{try{
const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
if(!tab?.id||!tab.url?.startsWith('https://'))throw Error('Apri una pagina HTTPS');
pageUrl=tab.url;
const [{result}]=await chrome.scripting.executeScript({target:{tabId:tab.id},func:()=>{
const seen=new Set(),items=[];
const visible=element=>{const style=getComputedStyle(element);const rect=element.getBoundingClientRect();return style.display!=='none'&&style.visibility!=='hidden'&&rect.width>0&&rect.height>0&&rect.bottom>0&&rect.top<innerHeight};
const walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
let node,visited=0;
while((node=walk.nextNode())&&visited++<18000){
 const el=node.parentElement;if(!el||!visible(el)||['SCRIPT','STYLE','NOSCRIPT','TEXTAREA','INPUT'].includes(el.tagName))continue;
 const raw=node.textContent.trim();
 if(!/buy\s*now|compra\s*ora/i.test(raw))continue;
 const button=el.closest('button,[role="button"]');
 const context=(button?.innerText||el.innerText||raw).replace(/\s+/g,' ').trim().slice(0,180);
 const match=context.match(/(?:buy\s*now|compra\s*ora)(?:\s*for|\s*a)?\s*([0-9][0-9.,]*)/i);
 if(!match)continue;
 const digits=match[1].replace(/[^0-9]/g,'');
 const value=Number(digits);
 if(!Number.isSafeInteger(value)||value<1||value>15000000)continue;
 const rect=(button||el).getBoundingClientRect();
 const key=[value,Math.round(rect.x),Math.round(rect.y)].join(':');
 if(seen.has(key))continue;seen.add(key);
 items.push({price:value,label:context.slice(0,90),x:Math.round(rect.x),y:Math.round(rect.y)});
 if(items.length>=50)break;
}
return items;
}});
detectedListings=Array.isArray(result)?result:[];
const selector=el('listings');selector.replaceChildren();
const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=detectedListings.length?'Scegli una delle '+detectedListings.length+' inserzioni':'Nessuna inserzione riconosciuta';selector.append(placeholder);
detectedListings.forEach((item,index)=>{const option=document.createElement('option');option.value=String(index);option.textContent=(index+1)+'. '+item.price.toLocaleString('it-IT')+' crediti · '+item.label.slice(0,50);selector.append(option)});
el('selected').textContent=detectedListings.length?detectedListings.map((item,index)=>(index+1)+'. '+item.label+' ['+item.x+','+item.y+']').join('\n'):'Nessun prezzo Compra ora numerico nel testo visibile';
el('status').textContent=detectedListings.length+' inserzioni leggibili. Seleziona la carta corretta; nome e ID EA vanno verificati manualmente.';
}catch(e){el('status').textContent='Lettura non riuscita: '+e.message}};
el('useListing').onclick=()=>{const index=el('listings').value;if(index===''||!detectedListings[Number(index)]){el('status').textContent='Seleziona prima una inserzione';return}el('buy').value=detectedListings[Number(index)].price;el('status').textContent='Prezzo trasferito. Verifica identità della carta e riferimento storico.'};
