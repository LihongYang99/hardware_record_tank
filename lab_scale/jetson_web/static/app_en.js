'use strict';
// English dashboard. Same API and data rules as app.js; only presentation text differs.
const $ = id => document.getElementById(id);
let series = [], history = [], refreshing = false, initialized = false;
const qcText = {UNVALIDATED:'Not yet validated',CONFIGURATION_MISMATCH:'Configuration mismatch',COMPENSATION_MISSING:'No temperature compensation',COMMUNICATION_ERROR:'Sensor communication error',SENSOR_FAULT:'Sensor fault',OUT_OF_RANGE:'Out of range',MISSING_VALUE:'Missing value',OK:'QC: OK'};
const labels = {'DO_SEN0681/DO_mg_L':'Dissolved oxygen','DO_SEN0681/saturation_pct':'DO saturation','DO_SEN0681/temperature_C':'Temp (DO probe)',
  'ORP_SEN0709/ORP_mV':'ORP','ORP_SEN0709/temperature_C':'Temp (ORP probe)','EC_ATLAS_EZO/EC_uS_cm':'Conductivity (EC)',
  'EC_ATLAS_EZO/salinity_PSU':'Salinity','PH_ATLAS_EZO/pH':'pH'};
const cameraText = {LIVE:'Live video',CONNECTING:'Connecting',RETRYING:'Connection lost · retrying',NOT_CONFIGURED:'Not configured',NO_GSTREAMER:'Decoder unavailable'};
const nodeName = node => node === 'shrimp-node01' ? 'Node 1' : 'Node 2';
const label = s => labels[s.sensor + '/' + s.parameter] || s.parameter;
function make(tag, cls, text) { const el=document.createElement(tag); if(cls) el.className=cls; if(text!==undefined) el.textContent=text; return el; }
function draw() {
  const canvas=$('chart'), ratio=window.devicePixelRatio||1, w=canvas.clientWidth, h=220;
  canvas.width=w*ratio; canvas.height=h*ratio;
  const ctx=canvas.getContext('2d'); ctx.scale(ratio,ratio); ctx.clearRect(0,0,w,h);
  const valid=history.filter(r=>r.value!==null&&['OK','UNVALIDATED'].includes(r.qc_flag));
  ctx.font='10px system-ui';ctx.fillStyle='#87958c';ctx.strokeStyle='#e5eae3';
  for(let i=0;i<4;i++){let y=20+i*52;ctx.beginPath();ctx.moveTo(45,y);ctx.lineTo(w-12,y);ctx.stroke();}
  if(!valid.length){ctx.textAlign='center';ctx.fillText('No plottable measurements yet',w/2,105);$('chartMessage').textContent=history.length?'Existing records carry an abnormal QC flag, so no line is drawn; raw values are in the CSV export.':'No measurements yet';return;}
  const values=valid.map(r=>r.value), low=Math.min(...values), high=Math.max(...values), pad=(high-low)*0.15||1;
  const min=low-pad,max=high+pad, t0=history[0].received_epoch,t1=history[history.length-1].received_epoch;
  const x=r=>45+(r.received_epoch-t0)/Math.max(1,t1-t0)*(w-57),y=r=>176-(r.value-min)/(max-min)*156;
  ctx.textAlign='right';for(let i=0;i<4;i++)ctx.fillText((max-(max-min)*i/3).toFixed(2),39,23+i*52);
  ctx.strokeStyle='#b28a36';ctx.lineWidth=2;let previous=null;
  for(const row of history){
    if(row.value===null||!['OK','UNVALIDATED'].includes(row.qc_flag)){previous=null;continue;}
    if(previous&&row.boot_id===previous.boot_id&&row.sequence_number===previous.sequence_number+1&&row.received_epoch-previous.received_epoch<=15){ctx.beginPath();ctx.moveTo(x(previous),y(previous));ctx.lineTo(x(row),y(row));ctx.stroke();}
    ctx.fillStyle='#b28a36';ctx.beginPath();ctx.arc(x(row),y(row),2,0,Math.PI*2);ctx.fill();previous=row;
  }
  ctx.fillStyle='#87958c';ctx.textAlign='left';ctx.fillText(new Date(t0*1000).toISOString().slice(11,19),45,207);ctx.textAlign='right';ctx.fillText(new Date(t1*1000).toISOString().slice(11,19)+' UTC',w-12,207);
  $('chartMessage').textContent='Gold points are recorded values (UNVALIDATED = not yet validated). The line breaks at abnormal QC, missing data and node restarts.';
}
async function loadHistory(){const s=series[Number($('series').value)||0];if(!s)return;const response=await fetch('/api/history?sensor='+encodeURIComponent(s.sensor)+'&parameter='+encodeURIComponent(s.parameter));if(!response.ok)throw Error('history');history=await response.json();draw();}
async function refresh(){
  if(refreshing)return;refreshing=true;
  try{
    const response=await fetch('/api/status');if(!response.ok)throw Error('status');const data=await response.json();
    $('serverDot').classList.add('connected');$('gateway').textContent='Jetson web service online';
    series=data.series;
    if(!initialized){series.forEach((s,i)=>{const option=make('option','',label(s)+' · '+nodeName(s.node));option.value=i;$('series').append(option);});initialized=true;}
    const waiting=[];
    for(const [node,config] of Object.entries(data.nodes)){
      const network=data.network[node]||{}, rows=data.latest.filter(r=>r.node_id===node), fresh=rows.filter(r=>!r.stale);
      const badge=$('status-'+node);badge.className='badge'+(fresh.length?' live':' warn');badge.textContent=fresh.length?'Receiving data':network.reachable&&network.identity_verified?'Online · no new data':'Network not confirmed';
      if(!fresh.length)waiting.push(nodeName(node));
      const container=$('metrics-'+node);container.replaceChildren();
      series.filter(s=>s.node===node).forEach(s=>{
        const row=rows.find(r=>r.sensor_id===s.sensor&&r.parameter===s.parameter),box=make('div','metric');
        box.append(make('div','metric-label',label(s)));const reading=make('div','reading',row&&row.value!==null?Number(row.value).toLocaleString('en-US',{maximumFractionDigits:3}):'—');reading.append(make('span','unit',s.unit));box.append(reading);
        box.append(make('div','qc',row?(row.stale?'STALE · ':'')+(qcText[row.qc_flag]||row.qc_flag):'Waiting for data'));
        box.append(make('div','source',s.sensor));container.append(box);
      });
      const last=rows.reduce((a,r)=>r.received_utc>a?r.received_utc:a,'');
      $('detail-'+node).textContent=config.ip+' · '+(network.identity_verified?'MAC verified':'MAC not verified')+' | Sample UTC: not synchronised'+(last?' | Last received: '+last:' | No records yet');
    }
    $('notice').textContent=(waiting.length?waiting.join(' and ')+' not delivering live data right now.':'Live data from both nodes. Check each reading’s QC flag and whether it is stale.')+' Probes are not yet calibrated; node clocks are not synchronised, so times shown are when the gateway received the data.'+(!data.metadata_configured?' Tank / experiment IDs are not configured yet.':'');
    $('count').textContent=data.stats.measurements;$('rawCount').textContent=data.stats.raw_records;$('issueCount').textContent=data.stats.issues;
    $('cameraStatus').textContent=cameraText[data.camera.code]||'Unknown';$('cameraStatus').className='badge'+(data.camera.live?' live':' warn');
    $('cameraEmpty').hidden=data.camera.live;$('cameraFrame').hidden=!data.camera.live;
    if(data.camera.live)$('cameraFrame').src='/camera.jpg?t='+Date.now();
    $('lastUpdate').textContent='Gateway time '+data.gateway_utc;
    await loadHistory();
  }catch(error){$('serverDot').classList.remove('connected');$('gateway').textContent='Connection to web service lost';$('notice').textContent='Cannot fetch the latest data. Readings on screen are old and must not be treated as live.';for(const node of ['shrimp-node01','shrimp-node02']){$('status-'+node).textContent='Disconnected · old values';$('status-'+node).className='badge warn';}$('cameraFrame').hidden=true;$('cameraEmpty').hidden=false;}
  finally{refreshing=false;}
}
$('cameraFrame').addEventListener('error',()=>{$('cameraFrame').hidden=true;$('cameraEmpty').hidden=false;$('cameraStatus').textContent='Frame unavailable';});
$('series').addEventListener('change',()=>loadHistory().catch(()=>{$('chartMessage').textContent='Failed to load history';}));window.addEventListener('resize',draw);
refresh();setInterval(refresh,2000);
