const $ = (id) => document.getElementById(id);

function showTab(name){
  document.querySelectorAll('.app-tab').forEach(s => s.style.display='none');
  document.querySelectorAll('.navbar-nav .nav-link').forEach(n=>n.classList.remove('active'));
  const link = document.querySelector(`.navbar-nav .nav-link[data-tab="${name}"]`);
  if(link) link.classList.add('active');
  const el = $(`tab-${name}`);
  if(el) el.style.display='block';

  // Only auto-load dashboard stuff if user manually clicks dashboard
  if(name==='dashboard') loadSummary();
  if(name==='highrisk' && !el.dataset.manual) loadSegmentCustomers('at_risk');
  if(name==='upsell') loadUpsell();
  if(name==='info') loadInfo();
}


showTab('welcome');

let latestSummary = null;

// =====================
// Segment labels & colors
// =====================
const SEGMENT_LABELS = {
  'mid_value': 'Low Risk',
  'high_value': 'High Risk',
  'at_risk': 'At Risk'
};

const SEGMENT_COLORS = {
  'mid_value': '#7c3aed',   // purple
  'high_value': '#9d4edd',  // deep purple
  'at_risk': '#f87171'      // soft red
};

async function loadSummary(){
  try {
    const res = await fetch('/api/summary');
    const data = await res.json();
    latestSummary = data;

    $('quick-snapshot').innerText = `${Object.values(data.segments).reduce((a,b)=>a+b,0)} accounts • ${data.top_risk.length} top risks`;
    $('kpi_count').innerText = Object.values(data.segments).reduce((a,b)=>a+b,0);
    $('kpi_highrisk').innerText = data.segments['at_risk'] || 0;
    $('kpi_upsell').innerText = data.upsell.length;

    renderTable('top_risk_table', data.top_risk, ['customer_id','company_name','segment','churn_prob'], 
      (r)=> `<span style="color:${r.churn_prob>0.6?'#dc2626':'#000'}">${(r.churn_prob*100).toFixed(1)}%</span>`,
      'Churn'
    );

    const segLabels = Object.keys(data.segments).map(k=>SEGMENT_LABELS[k] || k);
    const segValues = Object.keys(data.segments).map(k=>data.segments[k]);
    const segColors = Object.keys(data.segments).map(k=>SEGMENT_COLORS[k] || '#888');

    Plotly.newPlot('segment_pie', [{
      values: segValues,
      labels: segLabels,
      type: 'pie',
      marker: { colors: segColors },
      textinfo: 'label+percent'
    }], {height:340, paper_bgcolor:'transparent'});

    // Updated click handler: use raw segment key
    document.getElementById('segment_pie').on('plotly_click', evt => {
      const rawKey = Object.keys(data.segments)[evt.points[0].pointNumber];
      updateHighRiskTab(rawKey);
    });

    renderTrendChart();
  } catch(err){
    console.error(err);
    $('top_risk_table').innerHTML="<div class='text-danger'>Failed to load summary.</div>";
  }
}

function renderTrendChart(){
  const trace = { x:['Jan','Feb','Mar','Apr','May','Jun'], y:[60,62,58,55,57,53], type:'scatter', fill:'tozeroy', line:{color:'#7c3aed'} };
  Plotly.newPlot('trend_chart',[trace], {height:240, margin:{t:10}});
}

function renderTable(containerId, rows, cols, valueTransform=null, lastColName=null){
  const container = $(containerId);
  if(!rows || rows.length===0){ container.innerHTML="<div class='text-muted'>No records.</div>"; return; }
  let html = `<div class="table-responsive"><table class="table table-sm"><thead><tr>`;
  cols.forEach(c=>html+=`<th>${c.replace(/_/g,' ')}</th>`);
  if(lastColName) html+=`<th>${lastColName}</th>`;
  html+=`</tr></thead><tbody>`;
  rows.forEach(r=>{
    html+=`<tr>`; 
    cols.forEach(c=>html+=`<td>${r[c]===null||r[c]===undefined?'':r[c]}</td>`);
    if(lastColName) html+=`<td>${valueTransform?r=valueTransform(r):''}</td>`;
    html+=`</tr>`;
  });
  html+=`</tbody></table></div>`;
  container.innerHTML = html;
}

async function updateHighRiskTab(segmentKey){
  const heading = $('highrisk_heading');
  heading.textContent = `${SEGMENT_LABELS[segmentKey] || segmentKey} Individuals`;
  heading.dataset.segment = segmentKey;

  const tabEl = $('tab-highrisk');
  tabEl.dataset.manual = true;  // mark as manual so showTab doesn't reload default 'at_risk'

  try{
    const res = await fetch(`/api/segment/${segmentKey}`);
    if(!res.ok){ 
      $('highrisk_table').innerHTML=`<div class="text-danger">No records for ${SEGMENT_LABELS[segmentKey] || segmentKey}</div>`; 
      return; 
    }
    const rows = await res.json();
    renderTable('highrisk_table', rows, ['customer_id','company_name','segment','churn_prob','engagement_score','last_interaction_date'],
      r=> `<span style="color:${r.churn_prob>0.6?'#dc2626':'#000'}">${(r.churn_prob*100).toFixed(1)}%</span>`,
      'Churn'
    );
  } catch(e){ 
    console.error(e); 
    $('highrisk_table').innerHTML="<div class='text-danger'>Failed to load segment customers.</div>"; 
  }

  showTab('highrisk');
}


async function loadSegmentCustomers(segment){
  return updateHighRiskTab(segment);
}

async function loadUpsell(){
  try{
    const res = await fetch('/api/upsell');
    const rows = await res.json();
    const container = $('upsell_cards');
    if(!rows || rows.length===0){ container.innerHTML="<div class='text-muted'>No upsell candidates.</div>"; return; }
    container.innerHTML = rows.map(r=>`
      <div class="col-md-6">
        <div class="card p-3 h-100">
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <h6 class="mb-1">${r.company_name}</h6>
              <small class="text-muted">ID: ${r.customer_id}</small>
            </div>
            <div class="text-end">
              <div style="color:#7c3aed; font-weight:700;">$${Math.round(r.monetary)}</div>
              <small class="text-muted">spend</small>
            </div>
          </div>
          <div class="mt-2">${r.recommendation || ''}</div>
        </div>
      </div>
    `).join('');
  }catch(e){ console.error(e); $('upsell_cards').innerHTML="<div class='text-danger'>Failed to load upsell candidates.</div>"; }
}

async function loadInfo(){
  try{
    const res = await fetch('/api/info'); const info = await res.json();
    $('info_content').innerHTML = `
      <div class="mb-3"><h6>${info.title}</h6><p>${info.subtitle}</p></div>
      <div class="mb-3"><strong>Contact info:</strong> ${info.contact.name} , ${info.contact.email}</div>
      <div class="mb-3"><h6>Notes:</h6><ul>${info.notes.map(n=>`<li>${n}</li>`).join('')}</ul></div>
      <div class="mb-3"><h6>Features:</h6><ul>${info.features.map(f=>`<li>${f}</li>`).join('')}</ul></div>
      <div class="mb-3"><h6>Tech Stack:</h6><ul>${info.tech_stack.map(t=>`<li>${t}</li>`).join('')}</ul></div>
    `;
  } catch(e){ $('info_content').innerHTML="<div class='text-danger'>Failed to load info.</div>"; }
}

$('chat-send').addEventListener('click', async ()=>{
  const q=$('chat-input').value.trim(); if(!q) return;
  const box=$('chatbox'); box.innerHTML+=`<div><strong>You:</strong> ${q}</div>`;
  $('chat-input').value='';
  try{
    const res = await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})});
    const j = await res.json();
    box.innerHTML+=`<div style="color:#7c3aed"><strong>Bot:</strong> <pre style="white-space:pre-wrap">${j.answer}</pre></div>`;
    box.scrollTop = box.scrollHeight;
  }catch(e){ box.innerHTML+='<div class="text-danger">Chat failed.</div>'; }
});

async function downloadSegmentCSV(segment){
  try{
    const res = await fetch(`/api/segment/${segment}`);
    if(!res.ok){ alert("No data"); return; }
    const rows = await res.json();
    const csv = toCSV(rows);
    const blob = new Blob([csv], {type:'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href=url; a.download=`${segment}_customers.csv`; a.click();
    URL.revokeObjectURL(url);
  }catch(e){ alert("Download failed"); }
}

function toCSV(objArray){
  if(!objArray || objArray.length===0) return "";
  const keys = Object.keys(objArray[0]);
  const lines = [keys.join(",")];
  objArray.forEach(o=>{ lines.push(keys.map(k=>`"${(o[k]||"").toString().replace(/"/g,'""')}"`).join(",")); });
  return lines.join("\n");
}

function refreshHighRisk(){ 
  const heading = $('highrisk_heading');
  const segment = heading.dataset.segment || 'at_risk';
  loadSegmentCustomers(segment); 
}
