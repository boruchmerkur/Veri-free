/* checkmysite.pro — AI agent leaderboard widget
   ONE script tag drops a live, self-updating AI leaderboard into any site:

     <div data-checkmysite-ai></div>
     <script src="https://checkmysite.pro/ai-widget.js" async></script>

   Data: arena.ai's agent leaderboard (1.2M+ real agent sessions), re-served
   as slim JSON by this site's own /api/ai-leaderboard function. The CDN
   refreshes from arena.ai every ~6 hours; the widget re-fetches on the same
   cadence while the page is open, so it updates itself with zero maintenance.

   Same conventions as embed.js: shadow root so host CSS can't break it,
   but it ADOPTS the host's --cms-* / --color-* custom properties when
   present, so it can look native on any site.

   Config via data- attributes on the mount element:
     data-top="12|all"        rows shown before the "show all" control (default 12)
     data-simplify="0"        show every variant (default: one model per lab)
     data-view="rank|best"    starting tab (default rank)
     data-accent="#39e0d0"    override accent colour
     data-title="..."         heading text
     data-compact="1"         tighter layout for sidebars
     data-endpoint="..."      override the data URL (testing/self-hosting)
*/
(function(){
'use strict';
var ORIGIN = (function(){
  var s = document.currentScript || (function(){ var a=document.getElementsByTagName('script'); return a[a.length-1]; })();
  try { return new URL(s.src).origin; } catch(e){ return 'https://checkmysite.pro'; }
})();
var REFRESH_MS = 6*60*60*1000;           // matches the function's CDN window

var SIGNALS = [
  { key:'task_outcome_explicit', label:'finishes the job',
    why:'Users most often confirm the task actually got done.', best:'max' },
  { key:'praise_complaint', label:'happiest users',
    why:'Best ratio of praise to complaints across real sessions.', best:'max' },
  { key:'steerability', label:'takes direction',
    why:'Responds best when users correct it mid-task.', best:'max' },
  { key:'bash_recovery_steps', label:'recovers from errors',
    why:'Digs out of failed terminal commands in the fewest steps.', best:'max' },
  { key:'tool_hallucination', label:'avoids imagined tools',
    why:'Least likely to call tools that don’t exist.', best:'max' }
];

function css(){ return `
:host{ all:initial; }
*{ box-sizing:border-box; }
.w{
  --bg:      var(--cms-bg, var(--color-bg, #080a0c));
  --panel:   var(--cms-panel, #0c1013);
  --text:    var(--cms-text, var(--color-text, #e9e7e0));
  --dim:     var(--cms-dim, #7b858a);
  --accent:  var(--cms-accent, var(--color-primary, #39e0d0));
  --warn:    var(--cms-warn, #ffa62e);
  --alert:   var(--cms-alert, #ff4b26);
  --rule:    var(--cms-rule, #1b2226);
  --font:    var(--cms-font, var(--font-sans, ui-sans-serif,system-ui,-apple-system,sans-serif));
  --mono:    var(--cms-mono, ui-monospace,'SF Mono',Menlo,monospace);
  font-family:var(--font); color:var(--text); background:var(--bg);
  border:1px solid var(--rule); border-radius:10px; padding:18px; max-width:720px;
}
.w.compact{ padding:12px; }
.hd{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:4px; }
.ti{ font-size:15px; font-weight:600; letter-spacing:-0.01em; }
.by{ font-family:var(--mono); font-size:9px; letter-spacing:0.12em; text-transform:uppercase; color:var(--dim); text-decoration:none; }
.by:hover{ color:var(--accent); }
.sub{ font-family:var(--mono); font-size:10px; color:var(--dim); margin-bottom:12px; line-height:1.6; }
.sub .stale{ color:var(--warn); }
.tabs{ display:flex; gap:6px; margin:10px 0 12px; flex-wrap:wrap; }
.tb{ font-family:var(--mono); font-size:10px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
  padding:6px 12px; background:transparent; color:var(--dim); border:1px solid var(--rule);
  border-radius:6px; cursor:pointer; transition:color .15s,border-color .15s; }
.tb:hover{ color:var(--text); }
.tb.on{ color:var(--accent); border-color:var(--accent); }
.opt{ margin-left:auto; display:inline-flex; align-items:center; gap:6px; font-family:var(--mono); font-size:10px;
  color:var(--dim); cursor:pointer; user-select:none; }
.opt input{ accent-color:var(--accent); margin:0; }
.rows{ display:flex; flex-direction:column; }
.r{ display:grid; grid-template-columns:26px minmax(0,1fr) 110px 64px; gap:10px; align-items:center;
  padding:8px 0; border-bottom:1px solid var(--rule); }
.compact .r{ grid-template-columns:22px minmax(0,1fr) 70px 56px; }
.r:last-child{ border-bottom:none; }
.rk{ font-family:var(--mono); font-size:11px; color:var(--dim); text-align:right; }
.r.top .rk{ color:var(--accent); }
.nm{ min-width:0; }
.nm a{ color:var(--text); text-decoration:none; font-size:13px; font-weight:600; }
.nm a:hover{ color:var(--accent); }
.nm .org{ display:block; font-family:var(--mono); font-size:9px; letter-spacing:0.08em; text-transform:uppercase; color:var(--dim); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bar{ height:6px; border-radius:3px; background:var(--panel); overflow:hidden; position:relative; }
.bar i{ display:block; height:100%; background:var(--accent); border-radius:3px; }
.r.neg .bar i{ background:var(--alert); opacity:0.75; }
.sc{ font-family:var(--mono); font-size:11px; text-align:right; color:var(--accent); white-space:nowrap; }
.sc small{ display:block; font-size:8px; color:var(--dim); }
.r.neg .sc{ color:var(--alert); }
.more{ margin-top:10px; width:100%; font-family:var(--mono); font-size:10px; letter-spacing:0.1em; text-transform:uppercase;
  padding:8px; background:transparent; color:var(--dim); border:1px dashed var(--rule); border-radius:6px; cursor:pointer; }
.more:hover{ color:var(--accent); border-color:var(--accent); }
.cards{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; }
.cd{ background:var(--panel); border:1px solid var(--rule); border-radius:8px; padding:12px; }
.cd .k{ font-family:var(--mono); font-size:9px; letter-spacing:0.12em; text-transform:uppercase; color:var(--dim); margin-bottom:6px; }
.cd .m{ font-size:14px; font-weight:600; }
.cd .m a{ color:var(--text); text-decoration:none; }
.cd .m a:hover{ color:var(--accent); }
.cd .v{ font-family:var(--mono); font-size:11px; color:var(--accent); margin-top:2px; }
.cd .g{ font-size:11px; line-height:1.6; color:var(--dim); margin-top:6px; }
.cd .al{ font-family:var(--mono); font-size:9px; letter-spacing:0.04em; color:var(--dim);
  margin-top:8px; padding-top:7px; border-top:1px solid var(--rule); }
.cd .al i{ font-style:normal; color:var(--accent); opacity:0.75; }
.msg{ font-family:var(--mono); font-size:11px; color:var(--dim); padding:14px 0; }
.ft{ margin-top:14px; display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap;
  font-family:var(--mono); font-size:9px; letter-spacing:0.1em; text-transform:uppercase; }
.ft a{ color:var(--dim); text-decoration:none; }
.ft a:hover{ color:var(--accent); }
@media(max-width:480px){ .r{ grid-template-columns:22px minmax(0,1fr) 60px; } .bar{ display:none; } }
`; }

function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]);}); }
function pct(v,d){ return (v>=0?'+':'−')+Math.abs(v*100).toFixed(d==null?1:d)+'%'; }
function when(iso){
  if(!iso) return '';
  var d=new Date(iso); if(isNaN(d)) return '';
  return d.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'});
}

/* one model per lab — the table is rank-sorted, so first hit per org wins */
function simplify(models){
  var seen={}, out=[];
  for(var i=0;i<models.length;i++){
    var o=models[i].org||'?';
    if(!seen[o]){ seen[o]=1; out.push(models[i]); }
  }
  return out;
}

/* For one signal: the best VARIANT of each lab, ranked. Always computed from
   the full model list — so the leader is the true global leader for that
   signal, and the runners-up are other labs' bests, never sibling variants. */
function bestPerLab(models, sig){
  var byOrg={};
  for(var i=0;i<models.length;i++){
    var m=models[i], v=m.signals && m.signals[sig.key];
    if(typeof v!=='number') continue;
    var o=m.org||'?';
    if(!(o in byOrg) || v>byOrg[o].v) byOrg[o]={m:m, v:v};
  }
  var arr=[];
  for(var k in byOrg) arr.push(byOrg[k]);
  arr.sort(function(a,b){ return b.v-a.v; });
  return arr;
}

function mount(el){
  if(el.__cmsAi) return; el.__cmsAi=true;
  var accent   = el.getAttribute('data-accent');
  var title    = el.getAttribute('data-title') || 'AI agent leaderboard';
  var compact  = el.hasAttribute('data-compact');
  var topAttr  = el.getAttribute('data-top') || (compact?'6':'12');
  var view     = (el.getAttribute('data-view')||'rank')==='best' ? 'best' : 'rank';
  var simple   = el.getAttribute('data-simplify')!=='0';   // one per lab by default
  var endpoint = el.getAttribute('data-endpoint') || (ORIGIN+'/api/ai-leaderboard');
  var expanded = topAttr==='all';
  var topN     = expanded ? Infinity : (parseInt(topAttr,10)||12);

  var root = el.attachShadow ? el.attachShadow({mode:'open'}) : el;
  var style=document.createElement('style'); style.textContent=css(); root.appendChild(style);
  var w=document.createElement('div'); w.className='w'+(compact?' compact':'');
  if(accent) w.style.setProperty('--cms-accent', accent);
  w.innerHTML =
    '<div class="hd"><span class="ti">'+esc(title)+'</span>'+
      '<a class="by" href="https://checkmysite.pro/ai/" target="_blank" rel="noopener">checkmysite.pro</a></div>'+
    '<div class="sub"></div>'+
    '<div class="tabs">'+
      '<button type="button" class="tb" data-v="rank">Ranking</button>'+
      '<button type="button" class="tb" data-v="best">Best at…</button>'+
      '<label class="opt"><input type="checkbox" '+(simple?'checked':'')+' /> one per lab</label>'+
    '</div>'+
    '<div class="body"><div class="msg">Loading live standings…</div></div>'+
    '<div class="ft"><span>data: <a href="https://arena.ai/leaderboard/agent" target="_blank" rel="noopener">arena.ai</a></span>'+
      '<a href="https://checkmysite.pro/ai/" target="_blank" rel="noopener">free checks by checkmysite.pro →</a></div>';
  root.appendChild(w);

  var sub=w.querySelector('.sub'), body=w.querySelector('.body'),
      tabs=w.querySelectorAll('.tb'), chk=w.querySelector('.opt input');
  var data=null, fetchedAt=0;

  function models(){
    if(!data) return [];
    return chk.checked ? simplify(data.models) : data.models;
  }

  function renderRank(){
    var list=models(), cut=Math.min(list.length, expanded?list.length:topN);
    var max=0;
    for(var i=0;i<list.length;i++) max=Math.max(max, Math.abs(list[i].score||0));
    var h='<div class="rows">';
    for(var i=0;i<cut;i++){
      var m=list[i], wPct=max? Math.max(3, Math.abs(m.score)/max*100) : 0;
      h+='<div class="r'+(m.score<0?' neg':'')+(m.rank<=3?' top':'')+'">'+
        '<span class="rk">'+m.rank+'</span>'+
        '<span class="nm">'+(m.url?'<a href="'+esc(m.url)+'" target="_blank" rel="noopener">'+esc(m.model)+'</a>':esc(m.model))+
          '<span class="org">'+esc(m.org||'')+(m.license?' · '+esc(m.license):'')+'</span></span>'+
        '<span class="bar"><i style="width:'+wPct.toFixed(1)+'%"></i></span>'+
        '<span class="sc">'+pct(m.score)+'<small>±'+(m.ci*100).toFixed(1)+'</small></span>'+
      '</div>';
    }
    h+='</div>';
    if(cut<list.length) h+='<button type="button" class="more">show all '+list.length+'</button>';
    body.innerHTML=h;
    var more=body.querySelector('.more');
    if(more) more.addEventListener('click',function(){ expanded=true; renderRank(); });
  }

  function renderBest(){
    var h='<div class="cards">';
    for(var i=0;i<SIGNALS.length;i++){
      var s=SIGNALS[i], labs=bestPerLab(data.models,s);
      if(!labs.length) continue;
      var b=labs[0];
      var also=labs.slice(1,3).map(function(x){ return esc(x.m.model)+' <i>'+pct(x.v)+'</i>'; }).join(' · ');
      h+='<div class="cd"><div class="k">'+esc(s.label)+'</div>'+
        '<div class="m">'+(b.m.url?'<a href="'+esc(b.m.url)+'" target="_blank" rel="noopener">'+esc(b.m.model)+'</a>':esc(b.m.model))+'</div>'+
        '<div class="v">'+pct(b.v)+' · '+esc(b.m.org||'')+'</div>'+
        '<div class="g">'+esc(s.why)+'</div>'+
        (also?'<div class="al">then: '+also+'</div>':'')+
      '</div>';
    }
    body.innerHTML=h+'</div>';
  }

  function render(){
    if(!data) return;
    for(var i=0;i<tabs.length;i++) tabs[i].className='tb'+(tabs[i].getAttribute('data-v')===view?' on':'');
    sub.innerHTML='1.2M+ real agent sessions · net improvement over baseline'+
      (data.updated?' · updated '+esc(when(data.updated)):'')+
      (data.stale?' <span class="stale">· cached copy</span>':'');
    if(view==='best') renderBest(); else renderRank();
  }

  function load(){
    fetch(endpoint,{mode:'cors'}).then(function(r){
      if(!r.ok) throw 0; return r.json();
    }).then(function(j){
      if(!j||!j.models||!j.models.length) throw 0;
      data=j; fetchedAt=Date.now(); render();
    }).catch(function(){
      if(data) return;   // keep showing what we have
      body.innerHTML='<div class="msg">Couldn’t reach the leaderboard — it’ll retry on its own.</div>';
      setTimeout(load, 60000);
    });
  }

  for(var i=0;i<tabs.length;i++) tabs[i].addEventListener('click',function(){ view=this.getAttribute('data-v'); render(); });
  chk.addEventListener('change', render);

  load();
  // self-update: re-fetch every 6h while open, and on return to a stale tab
  setInterval(function(){ load(); }, REFRESH_MS);
  document.addEventListener('visibilitychange', function(){
    if(!document.hidden && Date.now()-fetchedAt > REFRESH_MS) load();
  });
}

function scan(){
  var nodes=document.querySelectorAll('[data-checkmysite-ai]');
  for(var i=0;i<nodes.length;i++) mount(nodes[i]);
}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', scan);
else scan();
window.CheckMySiteAI = { mount: scan };
})();
