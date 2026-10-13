'use strict';
// Login-protected device control, shared by /control (中文) and /control/en (English).
// The server checks the session and waits for each device's own reply.
// Devices come from /api/session (pump_ctl.DEVICES); each kind has one card builder below.
const $ = id => document.getElementById(id);
const EN = document.documentElement.lang === 'en';
// Temperatures are stored in °C; pages show both. cf = a temperature, df = a temperature difference (no +32).
const cf = c => Number(c).toFixed(1) + ' °C / ' + (Number(c) * 1.8 + 32).toFixed(1) + ' °F';
const df = d => Number(d) + ' °C / ' + (Number(d) * 1.8).toFixed(1) + ' °F';
const T = EN ? {
  result: {OK:'Accepted by the device',ER:'Rejected by the device',PUMP_NOT_READY:'Device not initialised yet, try again shortly',ANOTHER_COMMAND_PENDING:'Previous command still running',
    DUPLICATE_ID:'Duplicate command ignored',NO_REPLY:'No reply from the node (offline?); check the state before retrying',BUSY:'Another web command is running',
    BROKER_UNAVAILABLE:'MQTT broker unavailable',WRONG:'Wrong account or password',LOCKED:'Too many wrong passwords; this account is locked for 60 s',NO_USERS:'No operator accounts yet',
    NOT_ENABLED:'Control not enabled',LOGIN_REQUIRED:'Session expired, please log in again',PENDING:'Pending',CANCELLED_PUMP_RESET:'Pump reset, command cancelled',
    CANCELLED_PUMP_BOOT:'Pump restarted, command cancelled',REPLY_TIMEOUT:'Device reply timed out',
    SENSOR_NOT_READY:'Probe circuit not initialised yet, try again shortly',NOT_ALLOWED:'Not allowed by the node firmware',
    K_NOT_10:'Set K=10 first (step 1)',DRY_FIRST:'Do the dry calibration first',LOW_FIRST:'Do the low point first, then the high point',
    MID_FIRST:'Do the pH 7 midpoint first (it must always be first and clears the other points)',NO_READING:'No reading from this probe yet; is Node 2 online?'},
  qc: {UNVALIDATED:'State consistent',STATE_MISMATCH:'INT pin disagrees with controller',MOTOR_VOLTAGE_LOW:'Motor voltage low',NOT_RUNNING_AS_COMMANDED:'Not running at the set rate',
    COMMUNICATION_ERROR:'Communication error',MISSING_VALUE:'Missing value'},
  kind: {pump:'Pump', ezo:'Calibration'}, device: 'Device', running: 'Running', stopped: 'Stopped', runningReport: 'Running (controller report)', noData: 'No recent data',
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
    calClear: 'Clear calibration', cal: ml => 'Calibrate (measured ' + ml + ' mL)', query: c => 'Query ' + c,
    RECORDING_ON: 'Start long-term recording', RECORDING_OFF: 'Stop long-term recording (keep 12 h)',
    'HEAT,ON': 'Heater on (thermostat)', 'HEAT,OFF': 'Heater off (thermostat)', HEATER_AUTO_ON: 'Automatic temperature control on', HEATER_AUTO_OFF: 'Automatic temperature control off',
    ezo: {'K,10': 'Set K=10', 'Cal,dry': 'Dry calibration', 'Cal,clear': 'Clear calibration', low: v => 'Low point ' + v, high: v => 'High point ' + v,
      mid: v => 'Midpoint ' + v, single: v => 'Single point ' + v}},
  rec: {cardEyebrow: 'GATEWAY · DATA RECORDING', eyebrow: 'Data recording', sensors: 'Sensor nodes', on: 'Recording: kept long-term', off: 'Not recording: kept 12 h only',
    note: 'Each node has its own switch; each pump has its own on its card. Data received while recording is on is kept permanently; while it is off it is deleted automatically after 12 hours (useful while debugging). Switching only affects data received from now on; nothing already kept is deleted.',
    start: 'Start long-term recording', stop: 'Stop (keep only 12 h)', confirmOn: 'Keep all data received from now on?',
    confirmOff: 'Data received from now on will be deleted after 12 hours. Continue?', done: 'Saved.'},
  heat: {eyebrow: 'NODE 7 · HEATER', title: 'Heater (water temperature control)', water: 'Water temperature (mean)', setpoint: 'Set temperature',
    relay: 'Relay CH1', on: 'Powered', off: 'Off', auto: 'Automatic control', autoOn: 'On', autoOff: 'Off (heater stays off)',
    enable: 'Turn automatic control on', disable: 'Turn automatic control off', save: 'Save temperature', setLabel: 'Set temperature (°C)',
    confirmEnable: t => 'Heat automatically whenever the water is below ' + cf(t) + '?', confirmDisable: 'Turn automatic control off? The heater will switch off.',
    range: (a, b) => 'Set temperature must be between ' + cf(a) + ' and ' + cf(b) + '.', needSetpoint: 'Save a set temperature first.',
    rule: h => 'Heats when the mean of the DO probe and turbidity probe temperatures is below the set temperature, stops at set + ' + df(h) + '. Any missing, stale or disagreeing probe (more than ' + df(3) + ' apart) switches the heater off; the relay also opens by itself 60 s after the gateway stops repeating ON. Relay state is the node\u2019s command state, not measured heater power.',
    reason: {BELOW_SETPOINT: 'Below set temperature: heating', AT_SETPOINT: 'At set temperature: off', HOLD: 'Within hysteresis: keeping state', DISABLED: 'Automatic control off',
      NO_SETPOINT: 'No set temperature', SOURCES_DISAGREE: 'Probes disagree by more than ' + df(3) + ': off'}, reasonPrefix: {NO_DATA: 'No valid reading from ', STALE: 'Stale reading from ', IMPLAUSIBLE: 'Implausible reading from '},
    broker: ' · MQTT broker unavailable (relay will open by itself)'},
  ezo: {reading: 'Current reading', spread: 'Movement, last ~1 min', cal: 'Calibration state', note: 'Standard, lot and temperature (required for every change)',
    notePlaceholder: 'e.g. Atlas 12,880 µS/cm, lot 1234, 22.4 °C', needNote: 'Write the standard, lot and temperature first (SPEC §41 record).',
    spreadNote: {ec: 'Atlas: stable within ±3 % (above 100 µS/cm)', ph: 'Rule of thumb: ≤ 0.02 pH over a minute'},
    calState: {ec: {'?CAL,0': 'Not calibrated', '?CAL,1': 'Dry + 1 solution', '?CAL,2': 'Dry + low + high'}, ph: {'?CAL,0': 'Not calibrated', '?CAL,1': 'Midpoint only', '?CAL,2': 'Two point', '?CAL,3': 'Three point'}},
    steps: {ec: {k10: '1 · Set K=10 (the probe is K 10)', dry: '2 · Dry calibration (probe dry, in air)', low: '3 · Low point µS/cm', high: '4 · High point µS/cm'},
      ph: {mid: '1 · Midpoint pH (always first)', low: '2 · Low point pH', high: '3 · High point pH'}},
    queries: {cal: 'Read Cal,?', k: 'Read K,?', slope: 'Read Slope,?'}, clear: 'Clear calibration',
    order: {ec: 'Order: K=10 → dry → 12,880 → 150,000 µS/cm. Rinse with distilled water and blot dry between solutions; wait until the reading is steady (1–2 min) before each point. The low point does not change the reading; the high point completes it. If the solution is not near 25 °C, enter the value printed on the bottle for its temperature.',
      ph: 'Order: 7.00 → 4.00 → 10.00. The midpoint must be first and erases earlier points. Rinse between buffers; wait until the reading is steady before each point. Use the bottle’s value for the buffer’s temperature.'},
    confirm: (name, step, value) => name + ': ' + step + (value !== undefined ? ' = ' + value : '') + '?\nThe probe must already be in this standard with a steady reading.',
    confirmClear: name => 'Erase the calibration of ' + name + '?', sending: 'Sent; a calibration step takes about 15 s (the node re-reads its state)…',
    after: 'after: ', before: 'reading before ', readingAfter: 'reading ', unit: {ec: 'µS/cm', ph: 'pH'}}
} : {
  result: {OK:'设备已接受',ER:'设备拒绝了这条命令',PUMP_NOT_READY:'设备还没初始化好，稍后再试',ANOTHER_COMMAND_PENDING:'上一条命令还没完成',
    DUPLICATE_ID:'重复命令，已忽略',NO_REPLY:'节点没有回复（可能离线）；先确认状态再重试',BUSY:'另一条网页命令正在执行',
    BROKER_UNAVAILABLE:'MQTT broker 不可用',WRONG:'账号或密码错误',LOCKED:'错误次数过多，该账号 60 秒后再试',NO_USERS:'还没有操作员账号',
    NOT_ENABLED:'控制未开启',LOGIN_REQUIRED:'登录已过期，请重新登录',PENDING:'等待中',CANCELLED_PUMP_RESET:'泵复位，命令已取消',
    CANCELLED_PUMP_BOOT:'泵重启，命令已取消',REPLY_TIMEOUT:'设备回复超时',
    SENSOR_NOT_READY:'探头电路还没初始化好，稍后再试',NOT_ALLOWED:'节点固件不接受这条命令',
    K_NOT_10:'先做第 1 步：设 K=10',DRY_FIRST:'先做干校准',LOW_FIRST:'先做低点，再做高点',
    MID_FIRST:'先做 pH 7 中点（中点必须第一个做，而且会清除其他点）',NO_READING:'还没有这支探头的读数，Node 2 在线吗？'},
  qc: {UNVALIDATED:'状态一致',STATE_MISMATCH:'INT 引脚与控制器不一致',MOTOR_VOLTAGE_LOW:'电机电压过低',NOT_RUNNING_AS_COMMANDED:'未按设定流量运行',
    COMMUNICATION_ERROR:'通信错误',MISSING_VALUE:'缺值'},
  kind: {pump:'泵', ezo:'校准'}, device: '设备', running: '运行中', stopped: '已停止', runningReport: '运行中（控制器报告）', noData: '无最新数据',
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
    calClear: '清除校准', cal: ml => '校准（实测 ' + ml + ' mL）', query: c => '查询 ' + c,
    RECORDING_ON: '开始长期记录', RECORDING_OFF: '停止长期记录（只留 12 小时）',
    'HEAT,ON': '加热器通电（自动控温）', 'HEAT,OFF': '加热器断电（自动控温）', HEATER_AUTO_ON: '打开自动控温', HEATER_AUTO_OFF: '关闭自动控温',
    ezo: {'K,10': '设 K=10', 'Cal,dry': '干校准', 'Cal,clear': '清除校准', low: v => '低点 ' + v, high: v => '高点 ' + v,
      mid: v => '中点 ' + v, single: v => '单点 ' + v}},
  rec: {cardEyebrow: '网关 · 数据记录', eyebrow: '数据记录', sensors: '传感器节点', on: '记录中：长期保存', off: '未记录：只留 12 小时',
    note: '每个节点单独记录；每台泵的开关在它自己的卡片上。开启时收到的数据永久保存；关闭时收到的数据 12 小时后自动删除（适合调试）。切换只影响之后收到的数据，已经保存的不会被删。',
    start: '开始长期记录', stop: '停止记录（只留 12 小时）', confirmOn: '从现在起收到的数据全部长期保存？',
    confirmOff: '从现在起收到的数据会在 12 小时后自动删除，继续？', done: '已保存。'},
  heat: {eyebrow: 'NODE 7 · 加热器', title: '加热器（水温控制）', water: '水温（平均）', setpoint: '设定温度',
    relay: '继电器 CH1', on: '通电', off: '断电', auto: '自动控温', autoOn: '开', autoOff: '关（加热器保持断电）',
    enable: '打开自动控温', disable: '关闭自动控温', save: '保存温度', setLabel: '设定温度（°C）',
    confirmEnable: t => '水温低于 ' + cf(t) + ' 时自动加热？', confirmDisable: '关闭自动控温？加热器会断电。',
    range: (a, b) => '设定温度必须在 ' + cf(a) + ' 到 ' + cf(b) + ' 之间。', needSetpoint: '请先保存设定温度。',
    rule: h => '水温取 DO 探头和浊度探头温度的平均值；低于设定温度时加热，达到设定 + ' + df(h) + ' 时停止。任一探头无数据、过期或两者相差超过 ' + df(3) + ' 都会断电；网关停止重复发送"开"后 60 秒，继电器也会自己断开。继电器状态是节点的控制状态，不是测得的加热功率。',
    reason: {BELOW_SETPOINT: '低于设定温度：加热中', AT_SETPOINT: '已达到设定温度：断电', HOLD: '在回差范围内：保持当前状态', DISABLED: '自动控温已关闭',
      NO_SETPOINT: '还没有设定温度', SOURCES_DISAGREE: '两个探头相差超过 ' + df(3) + '：断电'}, reasonPrefix: {NO_DATA: '没有有效读数：', STALE: '读数过期：', IMPLAUSIBLE: '读数不合理：'},
    broker: ' · MQTT broker 不可用（继电器会自己断开）'},
  ezo: {reading: '当前读数', spread: '最近约 1 分钟波动', cal: '校准状态', note: '标准液、批号、液温（每次改设置/校准必填）',
    notePlaceholder: '例如 Atlas 12,880 µS/cm，批号 1234，22.4 °C', needNote: '请先填写标准液、批号和液温（SPEC §41 校准记录）。',
    spreadNote: {ec: 'Atlas：±3 % 以内算稳定（100 µS/cm 以上）', ph: '经验值：1 分钟内变化 ≤ 0.02'},
    calState: {ec: {'?CAL,0': '未校准', '?CAL,1': '干 + 1 种液', '?CAL,2': '干 + 低 + 高'}, ph: {'?CAL,0': '未校准', '?CAL,1': '只有中点', '?CAL,2': '两点', '?CAL,3': '三点'}},
    steps: {ec: {k10: '1 · 设 K=10（探头是 K 10）', dry: '2 · 干校准（探头擦干，放在空气中）', low: '3 · 低点 µS/cm', high: '4 · 高点 µS/cm'},
      ph: {mid: '1 · 中点 pH（必须第一个）', low: '2 · 低点 pH', high: '3 · 高点 pH'}},
    queries: {cal: '查询 Cal,?', k: '查询 K,?', slope: '查询 Slope,?'}, clear: '清除校准',
    order: {ec: '顺序：K=10 → 干校准 → 12,880 → 150,000 µS/cm。换液之间用蒸馏水冲洗并吸干；每一点都等读数稳定（1–2 分钟）再按。做完低点读数不会变，做完高点才完成。液温离 25 °C 较远时，填瓶身温度表上对应液温的数值。',
      ph: '顺序：7.00 → 4.00 → 10.00。中点必须第一个做，并且会清除之前的校准点。换液之间冲洗；每一点等读数稳定再按。按瓶身温度表填缓冲液当前温度下的数值。'},
    confirm: (name, step, value) => name + '：' + step + (value !== undefined ? ' = ' + value : '') + '？\n探头必须已经放在这种标准液里，读数已稳定。',
    confirmClear: name => '确定清除' + name + '的校准？', sending: '已发送；校准步骤约需 15 秒（节点会重新读取状态）…',
    after: '之后：', before: '校准前读数 ', readingAfter: '读数 ', unit: {ec: 'µS/cm', ph: 'pH'}}
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
  if ((m = /^(EC|PH):(.*)$/.exec(command))) {
    const E = D.ezo, c = m[2], who = m[1] === 'EC' ? 'EC ' : 'pH '; let n;
    if (E[c]) return who + E[c];
    if ((n = /^Cal,(low|high|mid),([\d.]+)$/.exec(c))) return who + E[n[1]](n[2]);
    if ((n = /^Cal,([\d.]+)$/.exec(c))) return who + E.single(n[1]);
    return who + D.query(c);
  }
  if ((m = /^DC,([\d.]+),\*$/.exec(command))) return D.start(Number(m[1]));
  if (command === 'X') return D.stop;
  if ((m = /^D,([\d.]+),([\d.]+)$/.exec(command))) return D.dispenseOver(Number(m[1]), Number(m[2]));
  if ((m = /^D,([\d.]+)$/.exec(command))) return D.dispense(Number(m[1]));
  if (command === 'Cal,clear') return D.calClear;
  if ((m = /^Cal,([\d.]+)$/.exec(command))) return D.cal(Number(m[1]));
  if ((m = /^HEATER_SETPOINT,([\d.]+)$/.exec(command))) return (EN ? 'Set temperature ' : '设定温度 ') + cf(m[1]);
  return D[command] || D.query(command);
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
  const toggle = recordSwitch(() => [device.node_id]);
  card.append(head, metrics, make('p','muted',T.flowNote), form, toggle.box);
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
    toggle.update();
  }};
}
// Data recording switch for a set of nodes: rows received while it is off are deleted after 12 h (server.py RECENT_ONLY_S).
let recordingMap = {}, nodeInfo = {};
function recordSwitch(getNodes) {
  const box = make('div','pump-control'), row = make('div','pump-buttons'), badge = make('span','badge','…'), button = make('button',''), message = make('p','pump-message');
  button.type = 'button'; message.setAttribute('role','status');
  row.append(badge, button); box.append(make('p','eyebrow',T.rec.eyebrow), row, message);
  let current = null;
  button.addEventListener('click', async () => {
    if (busy || !user || current === null || !confirm(current ? T.rec.confirmOff : T.rec.confirmOn)) return;
    busy = true; controls();
    try {
      const {status, data} = await api('/api/recording', {on: !current, nodes: getNodes()});
      if (status === 401) { await checkSession(); return; }
      message.textContent = status === 200 ? T.rec.done : T.result[data.error] || data.error || T.failed;
    } catch (error) { message.textContent = T.failed; }
    finally { busy = false; controls(); refresh().catch(() => {}); }
  });
  return {box, update() {
    const nodes = getNodes().filter(n => n in recordingMap);
    current = nodes.length ? nodes.every(n => recordingMap[n]) : null;
    badge.className = 'badge' + (current ? ' live' : ' warn'); badge.textContent = current === null ? '…' : current ? T.rec.on : T.rec.off;
    button.textContent = current ? T.rec.stop : T.rec.start; button.className = current ? 'stop' : '';
  }};
}
const pumpNodes = () => devices.filter(d => d.kind === 'pump').map(d => d.node_id);
const sensorNodes = () => Object.keys(recordingMap).filter(n => !pumpNodes().includes(n) && n !== 'shrimp-node07');
function sensorRecordingCard() {
  const card = make('article','panel device-card'), names = make('p','muted'), toggle = recordSwitch(sensorNodes);
  card.append(make('p','eyebrow',T.rec.cardEyebrow), make('h2','',T.rec.sensors), names, make('p','muted',T.rec.note), toggle.box);
  return {card, update() { names.textContent = sensorNodes().map(n => (nodeInfo[n] || {}).name || n).join(' · '); toggle.update(); }};
}
const recorder = sensorRecordingCard();
// Node 7 heater: thermostat settings are stored on the gateway (heater_ctl.py); the decision runs there every 10 s.
function heaterCard() {
  const H = T.heat, card = make('article','panel device-card'), head = make('div','panel-head'), title = make('div'), badge = make('span','badge','…');
  title.append(make('p','eyebrow',H.eyebrow), make('h2','',H.title)); head.append(title, badge);
  const water = metric(H.water), target = metric(H.setpoint), relay = metric(H.relay), metrics = make('div','metrics');
  metrics.append(water.box, target.box, relay.box);
  const form = make('form','pump-control'), fieldsBox = make('div','pump-fields one'), label = make('label','',H.setLabel), input = make('input');
  Object.assign(input, {type:'number', step:'0.1', value:'15'}); const fahrenheit = make('span','muted');
  const showF = () => { fahrenheit.textContent = input.value === '' ? '' : '= ' + cf(input.value); };
  label.append(input, fahrenheit); fieldsBox.append(label);
  const buttons = make('div','pump-buttons'), save = make('button','',H.save), toggleAuto = make('button','');
  save.type = 'submit'; toggleAuto.type = 'button'; buttons.append(save, toggleAuto);
  const reason = make('p','muted'), message = make('p','pump-message'); message.setAttribute('role','status');
  const rule = make('p','muted'), toggle = recordSwitch(() => ['shrimp-node07']);
  form.append(fieldsBox, buttons, reason, message);
  card.append(head, metrics, rule, form, toggle.box);
  let state = {}, edited = false;
  input.addEventListener('input', () => { edited = true; showF(); });
  async function send(body) {
    if (busy || !user) return;
    busy = true; controls();
    try {
      const {status, data} = await api('/api/heater', body);
      if (status === 401) { await checkSession(); return; }
      message.textContent = status === 200 ? T.rec.done : T.result[data.error] || data.error || T.failed;
      if (status === 200) edited = false;
    } catch (error) { message.textContent = T.failed; }
    finally { busy = false; controls(); refresh().catch(() => {}); }
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    const [low, high] = state.setpoint_range_C || [5, 32], value = Number(input.value);
    if (!(value >= low && value <= high)) { message.textContent = H.range(low, high); return; }
    send({setpoint: value});
  });
  toggleAuto.addEventListener('click', () => {
    if (!state.enabled && state.setpoint_C == null) { message.textContent = H.needSetpoint; return; }
    if (confirm(state.enabled ? H.confirmDisable : H.confirmEnable(state.setpoint_C))) send({enabled: !state.enabled});
  });
  return {card, update(heater, rows) {
    if (!heater) return;
    state = heater;
    const relayRow = rows.find(r => r.sensor_id === 'HEATER_RELAY' && r.parameter === 'relay_on'), stale = !relayRow || relayRow.stale;
    const sources = Object.entries(heater.sources || {}).map(([s, v]) => s.split('_')[0] + ' ' + cf(v)).join(' · ');
    water.set(heater.temperature_C == null ? '—' : heater.temperature_C.toFixed(2), heater.temperature_C == null ? '°C' : '°C / ' + (heater.temperature_C * 1.8 + 32).toFixed(2) + ' °F', sources || T.waiting);
    target.set(heater.setpoint_C == null ? '—' : Number(heater.setpoint_C).toFixed(1), heater.setpoint_C == null ? '°C' : '°C / ' + (heater.setpoint_C * 1.8 + 32).toFixed(1) + ' °F', H.auto + (EN ? ': ' : '：') + (heater.enabled ? H.autoOn : H.autoOff));
    relay.set(relayRow && relayRow.value !== null ? (relayRow.value ? H.on : H.off) : '—', '', stale ? T.noData : '');
    if (!edited && heater.setpoint_C != null) input.value = heater.setpoint_C;
    showF();
    const [low, high] = heater.setpoint_range_C || [5, 32]; input.min = low; input.max = high;
    const [kind, sensor] = String(heater.reason || '').split(':');
    reason.textContent = (sensor ? (H.reasonPrefix[kind] || kind) + sensor : H.reason[kind] || kind) + (heater.error ? H.broker : '');
    rule.textContent = H.rule(heater.hysteresis_C);
    toggleAuto.textContent = heater.enabled ? H.disable : H.enable; toggleAuto.className = heater.enabled ? 'stop' : '';
    badge.className = 'badge' + (heater.heat ? ' live' : ' warn'); badge.textContent = heater.heat ? H.on : H.off;
    toggle.update();
  }};
}
const heaterBox = heaterCard();
// Node 2 EZO calibration (ezo_cal.py): one card per circuit; each step is one whitelisted command.
const EZO_STEPS = {ec: [['k10'], ['dry'], ['low', '12880'], ['high', '150000']], ph: [['mid', '7.00'], ['low', '4.00'], ['high', '10.00']]};
const EZO_READING = {ec: 'EC_uS_cm', ph: 'pH'}, EZO_QUERIES = {ec: ['cal', 'k'], ph: ['cal', 'slope']};
function ezoCard(device, index) {
  const E = T.ezo, id = device.id, name = nameOf(device), card = make('article','panel device-card'), head = make('div','panel-head'), title = make('div');
  title.append(make('p','eyebrow',T.device + ' ' + String(index + 1).padStart(2,'0') + ' · ' + T.kind.ezo), make('h2','',name),
    make('p','muted',EN ? device.description_en || device.description : device.description));
  const badge = make('span','badge','…'); head.append(title, badge);
  const reading = metric(E.reading), spread = metric(E.spread), cal = metric(E.cal), metrics = make('div','metrics');
  metrics.append(reading.box, spread.box, cal.box);
  const noteBox = make('div','pump-fields wide'), noteLabel = make('label','',E.note), note = make('input');
  Object.assign(note, {maxLength: 300, placeholder: E.notePlaceholder}); noteLabel.append(note); noteBox.append(noteLabel);
  const steps = make('div'), message = make('p','pump-message'); message.setAttribute('role','status');
  for (const [action, value] of EZO_STEPS[id]) {
    const row = make('div','pump-buttons'), button = make('button','',E.steps[id][action]); button.type = 'button';
    let input = null;
    if (value !== undefined) { input = make('input'); Object.assign(input, {type: 'number', step: 'any', value}); row.append(input); }
    row.append(button); steps.append(row);
    button.addEventListener('click', () => send(action, input ? input.value : undefined, E.steps[id][action]));
  }
  const tools = make('div','pump-buttons');
  for (const q of EZO_QUERIES[id]) { const b = make('button','',E.queries[q]); b.type = 'button'; b.addEventListener('click', () => send('query:' + q)); tools.append(b); }
  const clear = make('button','stop',E.clear); clear.type = 'button'; clear.addEventListener('click', () => send('clear', undefined, E.clear)); tools.append(clear);
  card.append(head, metrics, make('p','muted',E.order[id]), noteBox, steps, tools, message);
  async function send(action, value, label) {
    if (busy || !user) return;
    const query = action.startsWith('query:');
    if (!query && !note.value.trim()) { message.textContent = E.needNote; note.focus(); return; }
    if (!query && !confirm(action === 'clear' ? E.confirmClear(name) : E.confirm(name, label, value))) return;
    busy = true; controls(); message.textContent = query ? T.sent(name) : E.sending;
    try {
      const body = {device: id, action}; if (value !== undefined) body.value = Number(value); if (!query) body.note = note.value.trim();
      const {status, data} = await api('/api/control', body);
      if (status === 401) { await checkSession(); return; }
      const code = data.result || data.error, reply = data.reply && data.reply !== 'NONE' ? data.reply : '';
      let text = (T.result[code] || code) + (reply ? T.replied + reply : '');
      if (data.post) text += ' · ' + (data.pre != null ? E.before + data.pre + ' · ' : '') + E.after + Object.entries(data.post).filter(([, v]) => v != null).map(([k, v]) => k === 'reading' ? E.readingAfter + v : v).join(' · ');
      message.textContent = text;
    } catch (error) { message.textContent = T.failed; }
    finally { busy = false; controls(); refresh().catch(() => {}); }
  }
  return {card, async update(rows) {
    const row = rows.find(r => r.node_id === device.node_id && r.sensor_id === device.sensor_id && r.parameter === EZO_READING[id]);
    const stale = !row || row.stale, meta = row && row.metadata || {}, state = meta.calibration_reply;
    reading.set(row && row.value !== null ? Number(row.value).toFixed(id === 'ec' ? 1 : 3) : '—', E.unit[id], row ? (stale ? T.stale : '') + row.qc_flag : T.waiting);
    cal.set(state ? (E.calState[id][String(state).toUpperCase()] || state) : '—', '', (state || '') + (id === 'ec' && meta.K ? ' · K=' + meta.K : ''));
    badge.className = 'badge' + (row && !stale ? ' live' : ' warn'); badge.textContent = !row || stale ? T.noData : (state || '');
    try {
      const {data} = await api('/api/history?sensor=' + device.sensor_id + '&parameter=' + EZO_READING[id]);
      const values = (Array.isArray(data) ? data : []).filter(r => r.value !== null).slice(-15).map(r => r.value);
      if (values.length < 2) { spread.set('—', '', E.spreadNote[id]); return; }
      const range = Math.max(...values) - Math.min(...values), mean = values.reduce((a, b) => a + b, 0) / values.length;
      spread.set(id === 'ec' ? (mean ? (100 * range / Math.abs(mean)).toFixed(1) : '—') : range.toFixed(3), id === 'ec' ? '%' : 'pH', E.spreadNote[id]);
    } catch (error) { spread.set('—', '', E.spreadNote[id]); }
  }};
}
const builders = {pump: pumpCard, ezo: ezoCard};
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
    $('devices').replaceChildren(recorder.card, ...cards.map(c => c.card), heaterBox.card);
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
  if (status.data.recording && typeof status.data.recording === 'object') { recordingMap = status.data.recording; nodeInfo = status.data.nodes || {}; }
  for (const c of cards) c.update(rows);
  recorder.update();
  heaterBox.update(status.data.heater, rows);
  heaterBox.card.hidden = !status.data.heater;
  const byId = Object.fromEntries(devices.map(d => [d.id, d])), body = $('events'); body.replaceChildren();
  for (const e of (Array.isArray(events.data) ? events.data : [])) {
    const tr = make('tr'), device = byId[e.device_id] || devices.find(d => d.node_id === e.node_id);
    const node = nodeInfo[e.node_id];
    for (const text of [e.sent_utc.replace('T',' ').slice(0,19), device ? nameOf(device) : node ? node.name : e.node_id, e.operator, describe(e.command),
      T.result[e.result] || e.result, e.reply && e.reply !== 'NONE' ? e.reply : '—']) tr.append(make('td','',text));
    tr.append(make('td','note',e.note || ''));
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
