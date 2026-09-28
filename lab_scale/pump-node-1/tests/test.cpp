#include <cassert>
#include <iostream>
#include <set>
#include "Arduino.h"
uint32_t fakeTime=0; int fakeINT=0;
struct FakeTelemetry {
  std::string out;
  size_t write(const uint8_t*p,size_t n){out.append((const char*)p,n);return n;}
  size_t write(uint8_t c){out+=char(c);return 1;}
  void serviceUSB(){}
} telemetry;
#include "../script/PMP_MQTT/PumpChannel.h"
BenchLog benchLog; char bootID[17]="test";
void run(PumpChannel&p,uint32_t ms){for(uint32_t i=0;i<ms;i+=10){fakeTime+=10;p.service();}}
bool has(const char*s){return telemetry.out.find(s)!=std::string::npos;}
size_t sent(const HardwareSerial&u,const std::string&c){size_t n=0;for(auto&x:u.commands)n+=x==c;return n;}
int main(){
  int on; double v;
  assert(pumpDispense("?D,*,1",on)&&on==1);
  assert(pumpDispense("?D,-40.50,0",on)&&on==0);
  assert(pumpDispense("?d,12.00,1",on)&&on==1);
  for(auto s:{"?D,1","?D,*,2","?D,,1","?D,abc,1","?D,*,1x","?PV,1,1",""})assert(!pumpDispense(s,on));
  assert(pumpField("?PV,13.86","?PV,",v)&&v==13.86);
  assert(pumpField("?TV,434.50","?TV,",v)&&v==434.5);
  for(auto s:{"?PV,","?PV,nan","?PV,1e3","?TV,5","?PV,12.1x"})assert(!pumpField(s,"?PV,",v));
  assert(pumpIdentity("?i,PMP,1.1")&&pumpIdentity("?I,PMP,2.0"));
  assert(!pumpIdentity("?I,pH,2.17")&&!pumpIdentity("?i,PMP,"));
  assert(!strcmp(pumpQC(1,1,12.1,80),"UNVALIDATED"));
  assert(!strcmp(pumpQC(1,0,12.1,80),"STATE_MISMATCH"));
  assert(!strcmp(pumpQC(1,1,0.2,80),"MOTOR_VOLTAGE_LOW"));
  assert(!strcmp(pumpQC(0,0,12.1,80),"NOT_RUNNING_AS_COMMANDED"));
  assert(!strcmp(pumpQC(0,0,0,0),"UNVALIDATED"));

  HardwareSerial pu; PumpChannel pump(pu,4,80.0); pump.begin(18,17);
  run(pump,8000); assert(pump.ready);
  pump.poll(1,8000); run(pump,2000);
  assert(has("command=DC,80.00,*"));
  assert(has("pump_on=1 int_pin=1 motor_V=12.10 total_volume_mL=5.25 target_mL_min=80.00 raw_D=?D,*,1 raw_PV=?PV,12.10 raw_TV=?TV,5.25 calibration_reply=?Cal,0 COMM=OK QC=UNVALIDATED"));
  // 12 V motor supply unplugged: the controller still reports dispensing.
  pu.motorV=0.3; pump.poll(2,12000); run(pump,2000); assert(has("QC=MOTOR_VOLTAGE_LOW"));
  // INT wire disagrees with the controller (e.g. not connected).
  pu.motorV=12.1; pu.intStuckLow=true; pump.poll(3,16000); run(pump,2000); assert(has("QC=STATE_MISMATCH"));
  pu.intStuckLow=false;
  // Datasheet 20-day continuous-mode reset: *RS, then the setpoint is re-sent after re-initialisation.
  pu.running=false; pu.inject("*RS\r"); run(pump,100); assert(!pump.ready&&pump.resets==1);
  run(pump,8000); assert(pump.ready);
  pump.poll(4,24000); run(pump,2000);
  assert(sent(pu,"DC,80.00,*")==2&&pu.running);
  // Setpoint rejected (*TOOFAST, *ER): stays online and reports the pump honestly as stopped.
  pu.running=false; pu.tooFast=true; pu.inject("*RS\r"); run(pump,8100); assert(pump.ready);
  pump.poll(5,32000); run(pump,2000);
  assert(has("event=CONTROL_REJECTED")&&pump.ready);
  assert(has("pump_on=0 int_pin=0")&&has("QC=NOT_RUNNING_AS_COMMANDED"));
  // Not re-sent within a minute while the pump keeps reporting stopped.
  pump.poll(6,36000); run(pump,2000); assert(sent(pu,"DC,80.00,*")==3);
  // No reply: communication error with no value, never a zero reading.
  pu.silent=true; pump.poll(7,40000); run(pump,2500);
  assert(!pump.ready&&has("COMM=ERROR QC=COMMUNICATION_ERROR reason=REPLY_TIMEOUT"));
  pu.silent=false; run(pump,20000); assert(pump.ready);
  // A different EZO circuit on the cable never becomes ready.
  pu.wrongID=true; pu.inject("*RS\r"); run(pump,30000); assert(!pump.ready&&has("WRONG_OR_MISSING_PMP_ID"));
  // Monitor-only mode never dispenses.
  HardwareSerial mu; PumpChannel monitor(mu,4,0.0); monitor.begin(18,17);
  run(monitor,8000); assert(monitor.ready); monitor.poll(1,fakeTime); run(monitor,2000);
  assert(has("pump_on=0 int_pin=0 motor_V=12.10 total_volume_mL=5.25 target_mL_min=0.00"));
  // Only documented read-only queries plus the one setpoint command ever reach the pump.
  const std::set<std::string> allowed={"C,0","*OK,1","i","Status","Cal,?","Dstart,?","DC,?","D,?","PV,?","TV,?"};
  for(auto&c:pu.commands)assert(allowed.count(c)||c=="DC,80.00,*");
  for(auto&c:mu.commands)assert(allowed.count(c));
  assert(!strcmp(pumpQC(0,0,0,0),"UNVALIDATED"));

  // Operator payload and command grammar (pump_ctl.py builds these).
  char id[21],op[25],cmd[40]; double rate=0;
  assert(pumpOperatorPayload("id=17 operator=li.hy-2 cmd=DC,50.00,*",id,op,cmd)&&!strcmp(id,"17")&&!strcmp(op,"li.hy-2")&&!strcmp(cmd,"DC,50.00,*"));
  for(auto s:{"cmd=X","id=1 operator=a b cmd=X","id=x operator=a cmd=X","id=1 operator=a cmd=","id=1 operator=a cmd=D, 5","id=1 operator=a cmd=A=B","id=123456789012345678901 operator=a cmd=X"})
    assert(!pumpOperatorPayload(s,id,op,cmd));
  assert(pumpOperatorKind("DC,50.00,*",rate)==OP_START&&rate==50);
  assert(pumpOperatorKind("X",rate)==OP_STOP&&pumpOperatorKind("D,10",rate)==OP_DISPENSE&&pumpOperatorKind("D,10,1",rate)==OP_DISPENSE);
  assert(pumpOperatorKind("Cal,9.8",rate)==OP_CALIBRATE&&pumpOperatorKind("Cal,clear",rate)==OP_CALIBRATE&&pumpOperatorKind("Cal,?",rate)==OP_QUERY);
  for(auto s:{"Factory","D,*","D,-*","D,-5","D,+5","D,0.1","DC,200,*","DC,50","DC,50,10","DC,-50,*","Dstart,*","Dstart,10","Baud,38400","I2C,100","Plock,1","Invert","Cal,-1","Cal,","Sleep","DC,1e2,*"})
    assert(pumpOperatorKind(s,rate)==OP_INVALID);

  // Operator commands on a live channel: start, duplicate, stop (ends on *DONE), dispense, calibrate.
  monitor.submit("id=1 operator=li cmd=DC,50.00,*"); run(monitor,500);
  assert(has("event=OPERATOR_DONE cmd_id=1 operator=li command=DC,50.00,* result=OK reply=NONE target_mL_min=50.00"));
  assert(monitor.target==50&&monitor.targetDirty&&mu.running);
  monitor.submit("id=1 operator=li cmd=X"); assert(has("cmd_id=1 operator=li command=X result=DUPLICATE_ID"));
  monitor.submit("id=2 operator=li cmd=X"); run(monitor,500);
  assert(has("cmd_id=2 operator=li command=X result=OK reply=*DONE,3.50 target_mL_min=0.00")&&!mu.running&&monitor.target==0);
  monitor.submit("id=3 operator=li cmd=D,10"); run(monitor,500);
  assert(has("cmd_id=3 operator=li command=D,10 result=OK")&&mu.running&&monitor.target==0);
  mu.inject("*DONE,10.00\r"); run(monitor,100); assert(has("event=DISPENSE_DONE"));
  monitor.submit("id=4 operator=li cmd=Cal,9.8"); run(monitor,6000);
  assert(has("cmd_id=4 operator=li command=Cal,9.8 result=OK")&&monitor.ready);
  assert(has("calibration_reply=?CAL,1 max_rate_reply=?MAXRATE,60.00"));
  // Without 12 V the pump refuses to start; the reason is kept with the command.
  mu.noMotor=true; monitor.submit("id=5 operator=li cmd=DC,50.00,*"); run(monitor,500);
  assert(has("cmd_id=5 operator=li command=DC,50.00,* result=ER reply=*UV,PUMPPWR,0.00"));
  mu.noMotor=false;
  // One command at a time; a pump reset cancels a queued command instead of running it late.
  monitor.submit("id=6 operator=li cmd=TV,?"); monitor.submit("id=7 operator=li cmd=PV,?");
  assert(has("cmd_id=7 operator=li command=PV,? result=ANOTHER_COMMAND_PENDING"));
  mu.inject("*RS\r"); run(monitor,50); assert(has("cmd_id=6 operator=li command=TV,? result=CANCELLED_PUMP_RESET"));
  pump.submit("id=8 operator=li cmd=X"); assert(has("cmd_id=8 operator=li command=X result=PUMP_NOT_READY"));
  // Invalid payloads never reach the pump.
  size_t sentBefore=mu.commands.size();
  for(auto s:{"id=9 operator=li cmd=Factory","id=10 operator=li cmd=D,*","id=11 operator=li cmd=Dstart,*","cmd=X"}) monitor.submit(s);
  run(monitor,6000); assert(has("event=OPERATOR_REJECTED_INVALID"));
  for(size_t i=sentBefore;i<mu.commands.size();++i) assert(allowed.count(mu.commands[i]));
  const std::set<std::string> operatorAllowed={"DC,50.00,*","X","D,10","Cal,9.8"};
  for(auto&c:mu.commands)assert(allowed.count(c)||operatorAllowed.count(c));
  std::cout<<"PASS: parsing, QC, init/identity, setpoint re-send, rejection, timeout, monitor-only, operator start/stop/dispense/calibrate, dedupe, cancel on reset, whitelist\n";
}
