'use strict';
// Login-protected device control, shared by /control (中文) and /control/en (English).
// The server checks the session and waits for each device's own reply.
// Devices come from /api/session (pump_ctl.DEVICES); each kind has one card builder below.
const $ = id => document.getElementById(id);
const EN = document.documentElement.lang === 'en';
const T = EN ? {
  result: {OK:'Accepted by the device',ER:'Rejected by the device',PUMP_NOT_READY:'Device not initialised yet, try again shortly',ANOTHER_COMMAND_PENDING:'Previous command still running',
    DUPLICATE_ID:'Duplicate command ignored',NO_REPLY:'No reply from the node (offline?); check the state before retrying',BUSY:'Another web command is running',
    BROKER_UNAVAILABLE:'MQTT broker unavailable',WRONG:'Wrong account or password',LOCKED:'Too many wrong passwords; this account is locked for 60 s',NO_USERS:'No operator accounts yet',
    NOT_ENABLED:'Control not enabled',LOGIN_REQUIRED:'Session expired, please log in again',PENDING:'Pending',CANCELLED_PUMP_RESET:'Pump reset, command cancelled',
    CANCELLED_PUMP_BOOT:'Pump restarted, command cancelled',REPLY_TIMEOUT:'Device reply timed out'},
  qc: {UNVALIDATED:'State consistent',STATE_MISMATCH:'INT pin disagrees with controller',MOTOR_VOLTAGE_LOW:'Motor voltage low',NOT_RUNNING_AS_COMMANDED:'Not running at the set rate',
    COMMUNICATION_ERROR:'Communication error',MISSING_VALUE:'Missing value'},
  kind: {pump:'Pump'}, device: 'Device', running: 'Running', stopped: 'Stopped', runningReport: 'Running (controller report)', noData: 'No recent data',
  waiting: 'Waiting for data', stale: 'Stale · ', state: 'Run state', setpoint: 'Flow setpoint', setpointNote: 'Stored on the node, restored after power loss',
  motor: 'Motor supply', motorNote: 'Below 10.8 V the motor cannot run properly', rate: 'Flow mL/min', start: 'Start / set rate', stop: 'Stop',
  maxRate: v => 'Maximum constant rate ' + v + ' mL/min (reported by the pump after calibration).', maxUnknown: 'Maximum constant rate unknown.',
  flowNote: 'Run state is the pump controller’s own report (D,?), cross-checked against its INT pin. There is no flow meter yet, so this does not prove water is moving through the bypass.',
  rateRange: max => 'Flow must be between 0.5 and ' + max + ' mL/min.', confirmStop: n => 'Stop ' + n + '?', confirmStart: (n, v) => 'Run ' + n + ' at ' + v + ' mL/min?',
  sent: n => 'Sent, waiting for ' + n + ' to answer…', replied: ' · device replied ', noPower: ' · 12 V supply missing', tooFast: ' · above the maximum constant rate',
  failed: 'Request failed: web service unreachable.', count: n => n + ' controllable device' + (n === 1 ? '' : 's'), operator: u => 'Operator ' + u, loggedOut: 'Not logged in',
  noUsers: 'No operator accounts yet: on the Jetson, in lab_scale/jetson_web, run python3 pump_ctl.py web-user add <account>.',
  notEnabled: 'Control is not enabled: start the web service with --pump-control. The monitoring page is not affected.',
  loggedIn: u => 'Logged in. Every action is logged with the operator (web-' + u + ') and the device reply.', pleaseLogin: 'Please log in. Monitoring data needs no login; see the monitoring page.',
  loggingIn: 'Logging in…', loginFailed: 'Login failed', gateway: 'Gateway time ', unreachable: 'Cannot reach the web service.',
  describe: {start: r => 'Start ' + r + ' mL/min', stop: 'Stop', dispenseOver: (ml, min) => 'Dispense ' + ml + ' mL over ' + min + ' min', dispense: ml => 'Dispense ' + ml + ' mL',
    calClear: 'Clear calibration', cal: ml => 'Calibrate (measured ' + ml + ' mL)', query: c => 'Query ' + c}
} : {
  result: {OK:'设备已接受',ER:'设备拒绝了这条命令',PUMP_NOT_READY:'设备还没初始化好，稍后再试',ANOTHER_COMMAND_PENDING:'上一条命令还没完成',
    DUPLICATE_ID:'重复命令，已忽略',NO_REPLY:'节点没有回复（可能离线）；先确认状态再重试',BUSY:'另一条网页命令正在执行',
    BROKER_UNAVAILABLE:'MQTT broker 不可用',WRONG:'账号或密码错误',LOCKED:'错误次数过多，该账号 60 秒后再试',NO_USERS:'还没有操作员账号',
    NOT_ENABLED:'控制未开启',LOGIN_REQUIRED:'登录已过期，请重新登录',PENDING:'等待中',CANCELLED_PUMP_RESET:'泵复位，命令已取消',
    CANCELLED_PUMP_BOOT:'泵重启，命令已取消',REPLY_TIMEOUT:'设备回复超时'},
  qc: {UNVALIDATED:'状态一致',STATE_MISMATCH:'INT 引脚与控制器不一致',MOTOR_VOLTAGE_LOW:'电机电压过低',NOT_RUNNING_AS_COMMANDED:'未按设定流量运行',
    COMMUNICATION_ERROR:'通信错误',MISSING_VALUE:'缺值'},
  kind: {pump:'泵'}, device: '设备', running: '运行中', stopped: '已停止', runningReport: '运行中（控制器报告）', noData: '无最新数据',
  waiting: '等待数据', stale: '数据过期 · ', state: '运行状态', setpoint: '设定流量', setpointNote: '节点保存的设定，断电后恢复',
  motor: '电机电压', motorNote: '低于 10.8 V 电机不能正常工作', rate: '流速 mL/min', start: '启动 / 改流速', stop: '停止',
  maxRate: v => '最大恒定流量 ' + v + ' mL/min（校准后由泵报告）。', maxUnknown: '最大恒定流量未知。',
  flowNote: '运行状态来自泵控制器（D,?）并与 INT 引脚交叉核对；尚无流量计，不能证明旁路里真的有水在流。',
  rateRange: max => '流速必须在 0.5 到 ' + max + ' mL/min 之间。', confirmStop: n => '确定停止' + n + '？', confirmStart: (n, v) => '确定让' + n + '以 ' + v + ' mL/min 运行？',
  sent: n => '已发送，等待' + n + '的回复…', replied: ' · 设备回复 ', noPower: ' · 12 V 没接或没电', tooFast: ' · 超过最大恒定流量',
  failed: '请求失败：网页服务不可达。', count: n => '共 ' + n + ' 台可控制设备', operator: u => '操作员 ' + u, loggedOut: '未登录',
  noUsers: '还没有操作员账号：在 Jetson 的 lab_scale/jetson_web 目录运行 python3 pump_ctl.py web-user add <账号>。',
  notEnabled: '控制未开启：网页服务需要加 --pump-control 启动。监控页不受影响。',
  loggedIn: u => '已登录。每条操作都会记录操作人（web-' + u + '）和设备的回复。', pleaseLogin: '请先登录。监控数据不需要登录，在监控页查看。',
  loggingIn: '正在登录…', loginFailed: '登录失败', gateway: '网关时间 ', unreachable: '网页服务连接失败。',
  describe: {start: r => '启动 ' + r + ' mL/min', stop: '停止', dispenseOver: (ml, min) => min + ' 分钟内输送 ' + ml + ' mL', dispense: ml => '输送 ' + ml + ' mL',
    calClear: '清除校准', cal: ml => '校准（实测 ' + ml + ' mL）', query: c => '查询 ' + c}
};
const nameOf = d => EN ? d.name_en || d.name : d.name;
let user = null, devices = [], busy = false, cards = [];
function make(tag, cls, text) { const el=document.createElement(tag); if(cls) el.className=cls; if(text!==undefined) el.textContent=text; return el; }
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  let data = {}; try { data = await response.json(); } catch (error) {}
  return {status: response.status, data};
}
// Operator commands in words; the raw command stays in the database and terminal log.
function describe(command) {
  const D = T.describe; let m;
  if ((m = /^DC,([\d.]+),\*$/.exec(command))) return D.start(Number(m[1]));
  if (command === 'X') return D.stop;
  if ((m = /^D,([\d.]+),([\d.]+)$/.exec(command))) return D.dispenseOver(Number(m[1]), Number(m[2]));
  if ((m = /^D,([\d.]+)$/.exec(command))) return D.dispense(Number(m[1]));
  if (command === 'Cal,clear') return D.calClear;
  if ((m = /^Cal,([\d.]+)$/.exec(command))) return D.cal(Number(m[1]));
  return D.query(command);
}
function controls() { for (const b of document.querySelectorAll('.device-card button')) b.disabled = busy || !user; }
function metric(label) {
  const box = make('div','metric'), reading = make('div','reading','—'), unit = make('span','unit'), note = make('div','qc',T.waiting);
  box.append(make('div','metric-label',label)); reading.append(unit); box.append(reading, note);
  return {box, set(value, unitText, noteText) { reading.firstChild.textContent = value; unit.textContent = unitText; note.textContent = noteText; }};
}
function pumpCard(device, index) {
  const name = nameOf(device), card = make('article','panel device-card'), head = make('div','panel-head'), title = make('div');
  title.append(make('p','eyebrow',T.device + ' ' + String(index + 1).padStart(2,'0') + ' · ' + (T.kind[device.kind] || device.kind)), make('h2','',name),
    make('p','muted',EN ? device.description_en || device.description : device.description));
  const badge = make('span','badge','…'); head.append(title, badge);
  const state = metric(T.state), target = metric(T.setpoint), volt = metric(T.motor), metrics = make('div','metrics');
  metrics.append(state.box, target.box, volt.box);
  const form = make('form','pump-control'), fieldsBox = make('div','pump-fields one'), label = make('label','',T.rate), rate = make('input');
  Object.assign(rate, {type:'number', min:'0.5', max:String(device.max_rate_mL_min || 105), step:'0.1', value:'40'}); label.append(rate); fieldsBox.append(label);
  const buttons = make('div','pump-buttons'), start = make('button','',T.start), stop = make('button','stop',T.stop);
  start.type = 'submit'; stop.type = 'button'; buttons.append(start, stop);
  const hint = make('p','muted', device.max_rate_mL_min ? T.maxRate(device.max_rate_mL_min) : T.maxUnknown);
  const message = make('p','pump-message'); message.setAttribute('role','status');
  form.append(fieldsBox, buttons, hint, message);
  card.append(head, metrics, make('p','muted',T.flowNote), form);
  async function send(action) {
    if (busy || !user) return;
    const value = Number(rate.value), max = Number(rate.max) || 105;
    if (action === 'start' && !(value >= 0.5 && value <= max)) { message.textContent = T.rateRange(max); return; }
    if (!confirm(action === 'stop' ? T.confirmStop(name) : T.confirmStart(name, value))) return;
    busy = true; controls(); message.textContent = T.sent(name);
    try {
      const {status, data} = await api('/api/control', {device: device.id, action, rate: value});
      if (status === 401) { await checkSession(); return; }
      const code = data.result || data.error, reply = data.reply && data.reply !== 'NONE' ? data.reply : '';
      let text = (T.result[code] || code) + (reply ? T.replied + reply : '');
      if (reply.startsWith('*UV,PUMPPWR')) text += T.noPower;
      if (reply === '*TOOFAST') text += T.tooFast;
      message.textContent = text;
    } catch (error) { message.textContent = T.failed; }
    finally { busy = false; controls(); refresh().catch(() => {}); }
  }
  form.addEventListener('submit', event => { event.preventDefault(); send('start'); });
  stop.addEventListener('click', () => send('stop'));
  return {card, update(rows) {
    const mine = rows.filter(r => r.node_id === device.node_id && r.sensor_id === device.sensor_id), get = p => mine.find(r => r.parameter === p);
    const on = get('pump_on'), motor = get('motor_V'), stale = !on || on.stale;
    const setpoint = on && on.metadata ? on.metadata.target_mL_min : undefined;
    state.set(on && on.value !== null ? (on.value ? T.running : T.stopped) : '—', '', on ? (stale ? T.stale : '') + (T.qc[on.qc_flag] || on.qc_flag) : T.waiting);
    target.set(setpoint !== undefined ? Number(setpoint).toFixed(2) : '—', 'mL/min', T.setpointNote);
    volt.set(motor && motor.value !== null ? Number(motor.value).toFixed(2) : '—', 'V', T.motorNote);
    badge.className = 'badge' + (on && !stale && on.value && on.qc_flag === 'UNVALIDATED' ? ' live' : ' warn');
    badge.textContent = !on || stale ? T.noData : on.value ? T.runningReport : T.stopped;
  }};
}
const builders = {pump: pumpCard};
async function checkSession() {
  const {data} = await api('/api/session');
  user = data.user || null;
  const enabled = !!data.enabled;
  for (const id of ['devicePanel','eventPanel']) $(id).hidden = !enabled || !user;
  $('loginPanel').hidden = !enabled || !!user; $('logout').hidden = !user;
  $('userLabel').textContent = user ? T.operator(user) : T.loggedOut;
  if (!enabled) $('notice').textContent = data.reason === 'NO_USERS' ? T.noUsers : T.notEnabled;
  else $('notice').textContent = user ? T.loggedIn(user) : T.pleaseLogin;
  const list = Array.isArray(data.devices) ? data.devices : [];
  if (JSON.stringify(list.map(d => d.id)) !== JSON.stringify(devices.map(d => d.id))) {
    devices = list; cards = devices.map((d, i) => (builders[d.kind] || (() => null))(d, i)).filter(Boolean);
    $('devices').replaceChildren(...cards.map(c => c.card));
    $('deviceCount').textContent = T.count(cards.length);
  }
  controls();
  if (user) await refresh();
}
async function refresh() {
  if (!user) return;
  const [status, events] = await Promise.all([api('/api/status'), api('/api/control/events')]);
  if (events.status === 401) return checkSession();
  const rows = status.data.latest || [];
  for (const c of cards) c.update(rows);
  const byId = Object.fromEntries(devices.map(d => [d.id, d])), body = $('events'); body.replaceChildren();
  for (const e of (Array.isArray(events.data) ? events.data : [])) {
    const tr = make('tr'), device = byId[e.device_id];
    for (const text of [e.sent_utc.replace('T',' ').slice(0,19), device ? nameOf(device) : e.node_id, e.operator, describe(e.command),
      T.result[e.result] || e.result, e.reply && e.reply !== 'NONE' ? e.reply : '—']) tr.append(make('td','',text));
    body.append(tr);
  }
  if (status.data.gateway_utc) $('lastUpdate').textContent = T.gateway + status.data.gateway_utc;
}
$('loginForm').addEventListener('submit', async event => {
  event.preventDefault();
  $('loginButton').disabled = true; $('loginMessage').textContent = T.loggingIn;
  try {
    const {data} = await api('/api/login', {username: $('username').value.trim(), password: $('password').value});
    $('loginMessage').textContent = data.user ? '' : T.result[data.error] || T.loginFailed;
  } catch (error) { $('loginMessage').textContent = T.failed; }
  finally { $('password').value = ''; $('loginButton').disabled = false; await checkSession().catch(() => {}); }
});
$('logout').addEventListener('click', async () => { await api('/api/logout', {}); await checkSession(); });
checkSession().catch(() => { $('notice').textContent = T.unreachable; });
setInterval(() => { if (user && !busy) refresh().catch(() => {}); }, 3000);
