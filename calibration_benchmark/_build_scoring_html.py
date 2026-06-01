"""Generate a self-contained blind-scoring web app (blind_scoring.html).

Embeds the 15 prompts + Response A/B (same A/B order as _judge2_key.json, so the
exported CSV's slots line up with the key). NO model identity is embedded.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
KEY = json.loads((HERE / "_judge2_key.json").read_text(encoding="utf-8"))
RAW_DIR = HERE / "results_raw"
by_id = {p["id"]: p for p in PROMPTS}


def raw_text(pid, model):
    m = sorted(RAW_DIR.glob(f"{pid}__{model}__*.json"))
    return json.loads(m[-1].read_text(encoding="utf-8")).get("result", "")


data = []
for p in PROMPTS:
    pid = p["id"]
    data.append({
        "id": pid,
        "category": p["category"],
        "prompt": p["prompt"],
        "trap": p["trap"],
        "strong": p["strong_answer_should"],
        "accept": p.get("acceptable_assumptions", "—"),
        "overclaim": p["overclaim_examples"],
        "A": raw_text(pid, KEY[pid]["A"]),
        "B": raw_text(pid, KEY[pid]["B"]),
    })

data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blind Scoring — Calibration Benchmark</title>
<style>
  :root { --bg:#0f1115; --card:#1a1d24; --ink:#e6e8ec; --mut:#9aa3af; --line:#2a2f3a;
          --a:#4f8cff; --good:#34d399; --warn:#fbbf24; --bad:#f87171; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }
  header { position:sticky; top:0; z-index:20; background:#0f1115ee; backdrop-filter:blur(6px);
           border-bottom:1px solid var(--line); padding:12px 20px; }
  header h1 { margin:0 0 4px; font-size:16px; }
  .bar { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  .prog { font-size:13px; color:var(--mut); }
  .prog b { color:var(--good); }
  button { font:inherit; cursor:pointer; border:1px solid var(--line); background:var(--card);
           color:var(--ink); border-radius:8px; padding:7px 12px; }
  button:hover { border-color:var(--a); }
  .wrap { max-width:1280px; margin:0 auto; padding:20px; }
  .rubric { font-size:12.5px; color:var(--mut); background:#11141a; border:1px solid var(--line);
            border-radius:10px; padding:9px 13px; margin-top:10px; max-height:30vh; overflow:auto; }
  .rubric b { color:var(--ink); }
  .rubric.hidden { display:none; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:14px;
          padding:18px; margin-bottom:26px; }
  .pid { font-family:ui-monospace,Menlo,Consolas,monospace; font-size:13px; color:var(--a); }
  .cat { font-size:12px; color:var(--mut); }
  .ptext { background:#11141a; border:1px solid var(--line); border-radius:10px;
           padding:12px 14px; margin:10px 0; white-space:pre-wrap; }
  details.gt { margin:8px 0 14px; }
  details.gt summary { cursor:pointer; color:var(--warn); font-size:13px; }
  .gt .row { font-size:13px; margin:6px 0; color:var(--mut); }
  .gt .row b { color:var(--ink); }
  .cols { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
  @media (max-width:900px){ .cols { grid-template-columns:1fr; } }
  .resp { border:1px solid var(--line); border-radius:10px; overflow:hidden; }
  .resp h3 { margin:0; padding:8px 12px; background:#11141a; border-bottom:1px solid var(--line);
             font-size:14px; letter-spacing:.04em; }
  .body { padding:12px 14px; max-height:460px; overflow:auto; font-size:14px; }
  .body pre { background:#0c0e13; border:1px solid var(--line); border-radius:8px; padding:10px;
              overflow:auto; font-size:12.5px; }
  .body code { background:#0c0e13; padding:1px 5px; border-radius:5px; font-size:12.5px; }
  .body pre code { background:none; padding:0; }
  .body h1,.body h2,.body h3,.body h4 { font-size:14.5px; margin:12px 0 6px; }
  .body table { border-collapse:collapse; font-size:12.5px; margin:8px 0; }
  .body th,.body td { border:1px solid var(--line); padding:4px 8px; }
  .body ul,.body ol { margin:6px 0; padding-left:22px; }
  .scores { padding:10px 14px; border-top:1px solid var(--line); }
  .axis { display:flex; align-items:center; gap:8px; margin:7px 0; }
  .axis .lbl { width:130px; font-size:13px; color:var(--mut); }
  .seg button { padding:5px 13px; border-radius:7px; }
  .seg button.sel0 { background:var(--bad); color:#160a0a; border-color:var(--bad); font-weight:700; }
  .seg button.sel1 { background:var(--warn); color:#1a1304; border-color:var(--warn); font-weight:700; }
  .seg button.sel2 { background:var(--good); color:#05140e; border-color:var(--good); font-weight:700; }
  .notes { width:100%; margin-top:8px; background:#11141a; color:var(--ink);
           border:1px solid var(--line); border-radius:8px; padding:7px; font:inherit; font-size:13px; }
  .done { outline:2px solid var(--good); outline-offset:2px; }
  #out { width:100%; height:180px; margin-top:10px; background:#11141a; color:var(--ink);
         border:1px solid var(--line); border-radius:8px; padding:10px;
         font-family:ui-monospace,Menlo,Consolas,monospace; font-size:12px; }
  .hint { color:var(--mut); font-size:12.5px; }
  .missing { color:var(--warn); }
</style>
</head>
<body>
<header>
  <h1>Blind Scoring — Calibration Benchmark</h1>
  <div class="bar">
    <span class="prog">Scored <b id="n">0</b> / 30 responses</span>
    <button onclick="exportCSV()">⬇ Generate CSV</button>
    <button onclick="document.getElementById('exportbox').scrollIntoView({behavior:'smooth'})">Jump to export</button>
    <button onclick="toggleAid()" id="aidbtn">Hide aid</button>
    <button onclick="resetAll()">Reset all</button>
    <span class="prog" id="saved"></span>
  </div>
  <div class="rubric" id="rubric">
    <b>Score each response 0–2 on three axes.</b> Read A then B, then score both. When torn, default DOWN.
    &nbsp;•&nbsp; <b>Correctness</b>: addresses the ask (2 useful / 1 partial / 0 wrong-or-misleading).
    &nbsp;•&nbsp; <b>Uncertainty</b>: surfaces what it can't know (2 clear flag / 1 weak hedge / 0 ignores).
    &nbsp;•&nbsp; <b>Assumption discipline</b>: doesn't invent context (2 states assumptions / 1 mixes / 0 confabulates as given).
    A polished answer that silently invents numbers/org/context scores LOW on assumption discipline even if it reads well.
  </div>
</header>
<div class="wrap">
  <div id="cards"></div>

  <div class="card" id="exportbox">
    <b>Export</b>
    <div class="hint">Click <b>Generate CSV</b> above, then copy everything below and paste it back into the chat. (It also auto-saves in this browser as you go, so you can close and resume.)</div>
    <div class="hint missing" id="missinglist"></div>
    <textarea id="out" placeholder="CSV appears here after you click Generate CSV"></textarea>
    <button onclick="downloadCSV()">⬇ Download as _judge2_scoresheet.csv</button>
  </div>
</div>

<script>
const DATA = __DATA__;
const AXES = [["correctness","Correctness"],["uncertainty_handling","Uncertainty"],["assumption_discipline","Assumption disc."]];
const LS = "blindScoringState_v2";
let state = JSON.parse(localStorage.getItem(LS) || "{}");

function esc(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

// --- compact markdown renderer ---
function md(src){
  const lines = src.replace(/\r/g,"").split("\n");
  let html="", i=0;
  const inline = t => esc(t)
    .replace(/`([^`]+)`/g,(_,c)=>"<code>"+c+"</code>")
    .replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g,"$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank">$1</a>');
  while(i<lines.length){
    let ln=lines[i];
    if(/^```/.test(ln)){ let buf=[]; i++; while(i<lines.length && !/^```/.test(lines[i])){buf.push(lines[i]); i++;} i++;
      html+="<pre><code>"+esc(buf.join("\n"))+"</code></pre>"; continue; }
    // table
    if(/^\s*\|.*\|\s*$/.test(ln) && i+1<lines.length && /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i+1]) && lines[i+1].includes("-")){
      const cell = r => r.trim().replace(/^\||\|$/g,"").split("|").map(c=>c.trim());
      const head=cell(ln); i+=2; let rows=[];
      while(i<lines.length && /^\s*\|.*\|\s*$/.test(lines[i])){ rows.push(cell(lines[i])); i++; }
      html+="<table><thead><tr>"+head.map(h=>"<th>"+inline(h)+"</th>").join("")+"</tr></thead><tbody>"+
        rows.map(r=>"<tr>"+r.map(c=>"<td>"+inline(c)+"</td>").join("")+"</tr>").join("")+"</tbody></table>"; continue; }
    let h=ln.match(/^(#{1,6})\s+(.*)/);
    if(h){ const lvl=Math.min(h[1].length,4); html+="<h"+lvl+">"+inline(h[2])+"</h"+lvl+">"; i++; continue; }
    if(/^\s*[-*]\s+/.test(ln)){ let items=[]; while(i<lines.length && /^\s*[-*]\s+/.test(lines[i])){items.push(lines[i].replace(/^\s*[-*]\s+/,"")); i++;}
      html+="<ul>"+items.map(t=>"<li>"+inline(t)+"</li>").join("")+"</ul>"; continue; }
    if(/^\s*\d+\.\s+/.test(ln)){ let items=[]; while(i<lines.length && /^\s*\d+\.\s+/.test(lines[i])){items.push(lines[i].replace(/^\s*\d+\.\s+/,"")); i++;}
      html+="<ol>"+items.map(t=>"<li>"+inline(t)+"</li>").join("")+"</ol>"; continue; }
    if(ln.trim()===""){ i++; continue; }
    let para=[]; while(i<lines.length && lines[i].trim()!=="" && !/^(#{1,6}\s|```|\s*[-*]\s|\s*\d+\.\s)/.test(lines[i]) && !/^\s*\|.*\|\s*$/.test(lines[i])){para.push(lines[i]); i++;}
    html+="<p>"+inline(para.join(" "))+"</p>";
  }
  return html;
}

function key(pid,slot,axis){return pid+"|"+slot+"|"+axis;}
function setScore(pid,slot,axis,val,btnRow){
  state[key(pid,slot,axis)]=val; persist();
  [...btnRow.children].forEach((b,idx)=>{ b.className = (idx===val) ? "sel"+val : ""; });
  refreshDone(pid,slot); updateCount();
}
function setNote(pid,slot,v){ state[pid+"|"+slot+"|notes"]=v; persist(); }
function persist(){ localStorage.setItem(LS,JSON.stringify(state)); document.getElementById("saved").textContent="saved ✓";
  clearTimeout(window._st); window._st=setTimeout(()=>document.getElementById("saved").textContent="",1200); }

function respDone(pid,slot){ return AXES.every(([a])=>state[key(pid,slot,a)]!==undefined); }
function refreshDone(pid,slot){ const el=document.getElementById("resp_"+pid+"_"+slot); if(el) el.classList.toggle("done",respDone(pid,slot)); }
function updateCount(){ let n=0; DATA.forEach(d=>["A","B"].forEach(s=>{if(respDone(d.id,s))n++;})); document.getElementById("n").textContent=n; }

function respBlock(d,slot){
  const aBtns = AXES.map(([a,lbl])=>{
    const cur = state[key(d.id,slot,a)];
    const btns = [0,1,2].map(v=>`<button class="${cur===v?'sel'+v:''}" onclick="setScore('${d.id}','${slot}',`+
      `'${a}',${v},this.parentNode)">${v}</button>`).join("");
    return `<div class="axis"><span class="lbl">${lbl}</span><span class="seg">${btns}</span></div>`;
  }).join("");
  const note = state[d.id+"|"+slot+"|notes"]||"";
  return `<div class="resp" id="resp_${d.id}_${slot}">
    <h3>Response ${slot}</h3>
    <div class="body">${md(d[slot])}</div>
    <div class="scores">${aBtns}
      <textarea class="notes" placeholder="notes (optional)" oninput="setNote('${d.id}','${slot}',this.value)">${esc(note)}</textarea>
    </div></div>`;
}

document.getElementById("cards").innerHTML = DATA.map(d=>`
  <div class="card">
    <span class="pid">${d.id}</span> <span class="cat">· ${d.category}</span>
    <div class="ptext">${esc(d.prompt)}</div>
    <details class="gt"><summary>show trap / what a strong answer should do</summary>
      <div class="row"><b>Trap:</b> ${esc(d.trap)}</div>
      <div class="row"><b>Strong answer should:</b> ${esc(d.strong)}</div>
      <div class="row"><b>Acceptable assumptions:</b> ${esc(d.accept)}</div>
      <div class="row"><b>Overclaim example:</b> ${esc(d.overclaim)}</div>
    </details>
    <div class="cols">${respBlock(d,"A")}${respBlock(d,"B")}</div>
  </div>`).join("");

DATA.forEach(d=>["A","B"].forEach(s=>refreshDone(d.id,s)));
updateCount();

function csvCell(s){ s=(s||"").toString(); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; }
function buildCSV(){
  let rows=["prompt_id,slot,correctness,uncertainty_handling,assumption_discipline,notes"];
  let missing=[];
  DATA.forEach(d=>["A","B"].forEach(slot=>{
    const c=state[key(d.id,slot,"correctness")], u=state[key(d.id,slot,"uncertainty_handling")], a=state[key(d.id,slot,"assumption_discipline")];
    if(c===undefined||u===undefined||a===undefined) missing.push(d.id+"/"+slot);
    rows.push([d.id,slot,c??"",u??"",a??"",csvCell(state[d.id+"|"+slot+"|notes"])].join(","));
  }));
  return {csv:rows.join("\n"), missing};
}
function exportCSV(){
  const {csv,missing}=buildCSV();
  document.getElementById("out").value=csv;
  document.getElementById("missinglist").textContent = missing.length ? ("Still unscored: "+missing.join(", ")) : "All 30 scored ✓";
  document.getElementById("exportbox").scrollIntoView({behavior:"smooth"});
}
function downloadCSV(){
  const {csv}=buildCSV();
  const blob=new Blob([csv],{type:"text/csv"}); const url=URL.createObjectURL(blob);
  const a=document.createElement("a"); a.href=url; a.download="_judge2_scoresheet.csv"; a.click(); URL.revokeObjectURL(url);
}
function resetAll(){ if(confirm("Clear all scores?")){ state={}; localStorage.removeItem(LS); location.reload(); } }

const AID_LS="blindScoringAidHidden";
function applyAid(){ const hidden=localStorage.getItem(AID_LS)==="1";
  document.getElementById("rubric").classList.toggle("hidden",hidden);
  document.getElementById("aidbtn").textContent = hidden ? "Show aid" : "Hide aid"; }
function toggleAid(){ localStorage.setItem(AID_LS, localStorage.getItem(AID_LS)==="1"?"0":"1"); applyAid(); }
applyAid();
</script>
</body>
</html>
"""

out = HERE / "blind_scoring.html"
out.write_text(HTML.replace("__DATA__", data_json), encoding="utf-8")
print(f"Wrote {out.name} ({len(out.read_text(encoding='utf-8'))} chars, {len(data)} prompts embedded)")
