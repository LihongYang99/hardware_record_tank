'use strict';
const $ = id => document.getElementById(id);
let series = [], history = [], refreshing = false, initialized = false;
const qcText = {UNVALIDATED:'尚未科学验证',CONFIGURATION_MISMATCH:'配置不匹配',COMPENSATION_MISSING:'缺少温度补偿',COMMUNICATION_ERROR:'传感器通信错误',SENSOR_FAULT:'传感器异常',OUT_OF_RANGE:'超出范围',MISSING_VALUE:'缺少测量值',OK:'QC: OK'};
function make(tag, cls, text) { const el=document.createElement(tag); if(cls) el.className=cls; if(text!==undefined) el.textContent=text; return el; }
function draw() {
  const canvas=$('chart'), ratio=window.devicePixelRatio||1, w=canvas.clientWidth, h=220;
  canvas.width=w*ratio; canvas.height=h*ratio;
  const ctx=canvas.getContext('2d'); ctx.scale(ratio,ratio); ctx.clearRect(0,0,w,h);
  const valid=history.filter(r=>r.value!==null&&['OK','UNVALIDATED'].includes(r.qc_flag));
  ctx.font='10px system-ui';ctx.fillStyle='#87958c';ctx.strokeStyle='#e5eae3';
  for(let i=0;i<4;i++){let y=20+i*52;ctx.beginPath();ctx.moveTo(45,y);ctx.lineTo(w-12,y);ctx.stroke();}
  if(!valid.length){ctx.textAlign='center';ctx.fillText('等待可绘制的真实测量数据',w/2,105);$('chartMessage').textContent=history.length?'现有记录带异常 QC，曲线留空；原始值可导出查看。':'尚无真实历史数据';return;}
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
  $('chartMessage').textContent='黄色点线表示记录值，UNVALIDATED 尚未验证；异常、缺测和重启处断开。';
}
async function loadHistory(){const s=series[Number($('series').value)||0];if(!s)return;const response=await fetch('/api/history?sensor='+encodeURIComponent(s.sensor)+'&parameter='+encodeURIComponent(s.parameter));if(!response.ok)throw Error('history');history=await response.json();draw();}
async function refresh(){
  if(refreshing)return;refreshing=true;
  try{
    const response=await fetch('/api/status');if(!response.ok)throw Error('status');const data=await response.json();
    $('serverDot').classList.add('connected');$('gateway').textContent='Jetson 网页服务在线';
    series=data.series;
    if(!initialized){series.forEach((s,i)=>{const option=make('option','',s.label+' · '+s.sensor);option.value=i;$('series').append(option);});initialized=true;}
    const waiting=[];
    for(const [node,config] of Object.entries(data.nodes)){
      const network=data.network[node]||{}, rows=data.latest.filter(r=>r.node_id===node), fresh=rows.filter(r=>!r.stale);
      const badge=$('status-'+node);badge.className='badge'+(fresh.length?' live':' warn');badge.textContent=fresh.length?'收到测量数据':network.reachable&&network.identity_verified?'网络在线 · 无新数据':'设备网络待确认';
      if(!fresh.length)waiting.push(node==='shrimp-node01'?'Node 1':'Node 2');
      const container=$('metrics-'+node);container.replaceChildren();
      series.filter(s=>s.node===node).forEach(s=>{
        const row=rows.find(r=>r.sensor_id===s.sensor&&r.parameter===s.parameter),box=make('div','metric');
        box.append(make('div','metric-label',s.label));const reading=make('div','reading',row&&row.value!==null?Number(row.value).toLocaleString('en-US',{maximumFractionDigits:3}):'—');reading.append(make('span','unit',s.unit));box.append(reading);
        box.append(make('div','qc',row?(row.stale?'STALE · ':'')+(qcText[row.qc_flag]||row.qc_flag):'等待真实数据'));
        box.append(make('div','source',s.sensor));container.append(box);
      });
      const last=rows.reduce((a,r)=>r.received_utc>a?r.received_utc:a,'');
      $('detail-'+node).textContent=config.ip+' · '+(network.identity_verified?'MAC 已核对':'MAC 待核对')+' ｜ 采样 UTC：未同步 / 未验证'+(last?' ｜ 最后接收：'+last:' ｜ 尚无测量记录');
    }
    $('notice').textContent=(waiting.length?waiting.join('、')+' 尚未接入实时测量。设备联网不代表数据已经发送。':'测量已接入；请同时检查每个传感器的 QC 和是否过期。')+' 采样时间未同步时不补造 UTC。'+(!data.metadata_configured?' 实验 / 水缸标识尚未配置。':'');
    $('count').textContent=data.stats.measurements;$('rawCount').textContent=data.stats.raw_records;$('issueCount').textContent=data.stats.issues;
    $('cameraStatus').textContent=data.camera.state;$('cameraStatus').className='badge'+(data.camera.live?' live':' warn');
    $('cameraEmpty').hidden=data.camera.live;$('cameraFrame').hidden=!data.camera.live;
    if(data.camera.live)$('cameraFrame').src='/camera.jpg?t='+Date.now();
    $('lastUpdate').textContent='网关时间 '+data.gateway_utc;
    await loadHistory();
  }catch(error){$('serverDot').classList.remove('connected');$('gateway').textContent='网页服务连接中断';$('notice').textContent='无法取得最新数据。页面上的旧读数不能视为实时测量。';for(const node of ['shrimp-node01','shrimp-node02']){$('status-'+node).textContent='连接中断 · 旧值';$('status-'+node).className='badge warn';}$('cameraFrame').hidden=true;$('cameraEmpty').hidden=false;}
  finally{refreshing=false;}
}
$('cameraFrame').addEventListener('error',()=>{$('cameraFrame').hidden=true;$('cameraEmpty').hidden=false;$('cameraStatus').textContent='视频帧不可用';});
$('series').addEventListener('change',()=>loadHistory().catch(()=>{$('chartMessage').textContent='历史读取失败';}));window.addEventListener('resize',draw);
refresh();setInterval(refresh,2000);
