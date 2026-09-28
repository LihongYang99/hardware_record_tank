#pragma once
#include <Arduino.h>
#include "PumpParse.h"
#include "BenchLog.h"
extern BenchLog benchLog;
extern char bootID[17];
// One UART command at a time: send, collect at most one data line, finish on *OK.
// Startup/control/operator commands and every unexpected line are logged as TX/RX; routine
// D,? / PV,? / TV,? replies are kept verbatim inside the one result line per poll.
class PumpChannel {
  HardwareSerial &u; const int intPin;
  char line[128]={}, data[48]={}, cmd[40]={}, rawD[48]={}, rawPV[48]={}, rawTV[48]={}, cal[24]="UNKNOWN", maxRate[24]="UNKNOWN";
  char opId[21]={}, opName[25]={}, opCmd[40]={}, recent[4][21]={};
  size_t used=0;
  uint32_t started=0,lastRX=0,waitUntil=0,retryAt=0,lastControl=0,requested=0,sampleRX=0;
  bool waiting=false,haveData=false,badLine=false,controlDue=true,opPending=false,opActive=false;
  int step=-1,pollStep=-1,on=0,intAtReply=0,lastOn=-1,opKind=OP_INVALID,recentNext=0;
  double motorV=NAN,total=NAN,opRate=0;
  void event(const char *what) {
    benchLog.print("node_id=shrimp-node04 boot_id=%s sensor=PUMP_ATLAS_PMP uptime_ms=%lu event=%s seq=%lu cycle=%lu",
      bootID,(unsigned long)millis(),what,(unsigned long)seq,(unsigned long)cycle);
  }
  void logHex(const char *what,const char *bytes,size_t n,bool terminated) {
    char hex[259]; const char *digits="0123456789ABCDEF";
    if (n>128) n=128;
    for(size_t i=0;i<n;++i) {uint8_t b=bytes[i];hex[2*i]=digits[b>>4];hex[2*i+1]=digits[b&15];}
    size_t k=2*n; if(terminated) {hex[k++]='0';hex[k++]='D';} hex[k]=0;
    benchLog.print("node_id=shrimp-node04 boot_id=%s sensor=PUMP_ATLAS_PMP rx_uptime_ms=%lu seq=%lu event=%s raw_hex=%s",
      bootID,(unsigned long)lastRX,(unsigned long)seq,what,hex);
  }
  void operatorLog(const char *what,const char *id,const char *op,const char *c,const char *result,const char *reply) {
    benchLog.print("node_id=shrimp-node04 boot_id=%s sensor=PUMP_ATLAS_PMP uptime_ms=%lu event=%s cmd_id=%s operator=%s command=%s result=%s reply=%s target_mL_min=%.2f",
      bootID,(unsigned long)millis(),what,id,op,c,result,reply,target);
  }
  void operatorDone(const char *result) {
    if (!opActive && !opPending) return;
    operatorLog("OPERATOR_DONE",opId,opName,opCmd,result,opActive && haveData?data:"NONE");
    opActive=opPending=false;
  }
  // Any pump reset, timeout or bad reply: re-verify identity before trusting the pump again.
  // A queued operator command is cancelled, never run late after a reset.
  void restart(uint32_t delayMs,const char *why) {
    operatorDone(why);
    waiting=false; pollStep=-1; ready=false; step=-1; lastOn=-1; controlDue=true; retryAt=millis()+delayMs;
  }
  void fail(const char *reason) {
    if (pollStep>=0) benchLog.print("node_id=shrimp-node04 boot_id=%s sensor=PUMP_ATLAS_PMP seq=%lu cycle=%lu request_uptime_ms=%lu UTC=UNSYNCED command=%s reply=%s COMM=ERROR QC=COMMUNICATION_ERROR reason=%s",
      bootID,(unsigned long)seq,(unsigned long)cycle,(unsigned long)requested,cmd,haveData?data:"NONE",reason);
    else event(reason);
    restart(15000,reason);
  }
  bool quiet() const { return pollStep>=1; }
  bool needsData() const { return strchr(cmd,'?') || !strcmp(cmd,"i") || !strcmp(cmd,"Status"); }
  void send(const char *s) {
    strncpy(cmd,s,sizeof(cmd)-1); haveData=false; data[0]=0; waiting=true; started=millis();
    if (!quiet()) benchLog.print("node_id=shrimp-node04 boot_id=%s sensor=PUMP_ATLAS_PMP event=TX command=%s uptime_ms=%lu seq=%lu",
      bootID,s,(unsigned long)started,(unsigned long)seq);
    u.print(s); u.write('\r');
  }
  void runOperator() {
    opPending=false; opActive=true; ++operatorCommands;
    // The operator's setpoint replaces the supervised one; dispensing a volume or stopping turns supervision off.
    if (opKind==OP_START) {target=opRate; targetDirty=true; controlDue=false; lastControl=millis();}
    else if (opKind==OP_STOP || opKind==OP_DISPENSE) {target=0; targetDirty=true;}
    operatorLog("OPERATOR_COMMAND",opId,opName,opCmd,"SENT","NONE");
    send(opCmd);
  }
  void report() {
    benchLog.print("node_id=shrimp-node04 boot_id=%s sensor=PUMP_ATLAS_PMP seq=%lu cycle=%lu scheduled_uptime_ms=%lu request_uptime_ms=%lu rx_uptime_ms=%lu UTC=UNSYNCED pump_on=%d int_pin=%d motor_V=%.2f total_volume_mL=%.2f target_mL_min=%.2f raw_D=%s raw_PV=%s raw_TV=%s calibration_reply=%s COMM=OK QC=%s validation=UNVALIDATED",
      bootID,(unsigned long)seq,(unsigned long)cycle,(unsigned long)scheduled,(unsigned long)requested,(unsigned long)sampleRX,
      on,intAtReply,motorV,total,target,rawD,rawPV,rawTV,cal,pumpQC(on,intAtReply,motorV,target));
    lastOn=on; pollStep=-1;
  }
  void finish() {
    waiting=false; waitUntil=millis()+100;
    if (pollStep==0) {controlDue=false; pollStep=1; return;}
    if (pollStep==1) {
      if (!pumpDispense(data,on)) {fail("BAD_D_REPLY"); return;}
      intAtReply=digitalRead(intPin)?1:0; sampleRX=lastRX; strcpy(rawD,data);
    } else if (pollStep==2) {
      if (!pumpField(data,"?PV,",motorV)) {fail("BAD_PV_REPLY"); return;}
      strcpy(rawPV,data);
    } else if (pollStep==3) {
      if (!pumpField(data,"?TV,",total)) {fail("BAD_TV_REPLY"); return;}
      strcpy(rawTV,data);
    }
    if (pollStep>=1) {++pollStep; return;}
    if (!strcmp(cmd,"i") && !pumpIdentity(data)) {fail("WRONG_OR_MISSING_PMP_ID"); return;}
    if (!strcmp(cmd,"Cal,?")) {
      if (strncasecmp(data,"?Cal,",5) || strlen(data)>=sizeof(cal)) {fail("BAD_CAL_REPLY"); return;}
      strcpy(cal,data);
    } else if (haveData && data[0]!='?') {fail("UNEXPECTED_REPLY"); return;}
    if (!strcmp(cmd,"DC,?") && strlen(data)<sizeof(maxRate)) strcpy(maxRate,data);
    ++step;
  }
  void onLine() {
    line[used]=0;
    bool unusable=badLine || strpbrk(line," =");
    bool code=line[0]=='*' && strcmp(line,"*OK");
    bool done=!strncmp(line,"*DONE",5);
    if (!(waiting && quiet()) || unusable || code) logHex("RX",line,used,true);
    if (unusable) {if (waiting) fail("INVALID_ASCII_OR_OVERLONG_LINE"); return;}
    if (!strcmp(line,"*RS") || !strcmp(line,"*RE")) {
      // *RS = pump reset (datasheet: after 20 days of continuous mode); *RE = pump boot complete.
      if (line[2]=='S') ++resets;
      event(line[2]=='S'?"PUMP_RESET":"PUMP_BOOT_READY"); restart(2000,line[2]=='S'?"CANCELLED_PUMP_RESET":"CANCELLED_PUMP_BOOT"); return;
    }
    if (step<0) return; // startup drain: never interpret
    if (!waiting) {event(done?"DISPENSE_DONE":"UNSOLICITED_LINE"); return;}
    if (opActive) {
      // Operator commands: keep the first reply/code line, finish on *OK or *ER (X may end with *DONE only).
      bool ok=!strcmp(line,"*OK") || (done && !strcmp(opCmd,"X"));
      if (ok || !strcmp(line,"*ER")) {
        if (done && !haveData) {strcpy(data,line); haveData=true;}
        bool calibrated=ok && opKind==OP_CALIBRATE;
        waiting=false; waitUntil=millis()+100;
        operatorDone(ok?"OK":"ER");
        if (calibrated) restart(100,"NONE"); // re-read Cal,? and the new maximum rate
        return;
      }
      // A reply line, or a refusal reason such as *TOOFAST / *UV,PUMPPWR; never a late *DONE from an earlier dispense.
      if (!haveData && !done && used<sizeof(data)) {strcpy(data,line); haveData=true;}
      if (code) event(done?"DISPENSE_DONE":"ASYNC_CODE");
      return;
    }
    if (!strcmp(line,"*ER")) {
      if (pollStep==0) {event("CONTROL_REJECTED"); waiting=false; controlDue=false; pollStep=1; waitUntil=millis()+100; return;}
      fail("COMMAND_ERROR"); return;
    }
    if (!strcmp(line,"*OK")) {
      if (needsData() && !haveData) {fail("OK_WITHOUT_DATA"); return;}
      finish(); return;
    }
    if (code) {event(done?"DISPENSE_DONE":"ASYNC_CODE"); return;} // *TOOFAST, *UV, *OV ...: raw already logged
    if (haveData) {fail("MULTIPLE_REPLY_LINES"); return;}
    if (used>=sizeof(data)) {fail("REPLY_TOO_LONG"); return;}
    strcpy(data,line); haveData=true;
  }
public:
  bool ready=false,targetDirty=false; uint32_t seq=0,cycle=0,scheduled=0,resets=0,controls=0,operatorCommands=0;
  // target > 0: keep the pump at this constant rate (DC,<rate>,*); 0: never start it on its own.
  double target;
  PumpChannel(HardwareSerial &uart,int interruptPin,double targetMlMin):u(uart),intPin(interruptPin),target(targetMlMin){}
  void begin(int rx,int tx) {
    pinMode(intPin,INPUT_PULLDOWN); // a disconnected INT wire reads 0 and shows up as STATE_MISMATCH
    u.setRxBufferSize(1024); u.begin(9600,SERIAL_8N1,rx,tx);
    retryAt=millis()+2000; // pump controller startup grace period
  }
  // Operator command from MQTT. QoS 1 may redeliver, so ids are de-duplicated; one command at a time.
  void submit(const char *payload) {
    char id[21]={},op[25]={},c[40]={}; double rate=0; int kind=OP_INVALID;
    if (pumpOperatorPayload(payload,id,op,c)) kind=pumpOperatorKind(c,rate);
    if (kind==OP_INVALID) {logHex("OPERATOR_REJECTED_INVALID",payload,strlen(payload),false); return;}
    for (auto &r:recent) if (!strcmp(r,id)) {operatorLog("OPERATOR_REJECTED",id,op,c,"DUPLICATE_ID","NONE"); return;}
    strcpy(recent[recentNext],id); recentNext=(recentNext+1)%4;
    const char *busy=!ready?"PUMP_NOT_READY":(opPending || opActive)?"ANOTHER_COMMAND_PENDING":nullptr;
    if (busy) {operatorLog("OPERATOR_REJECTED",id,op,c,busy,"NONE"); return;}
    strcpy(opId,id); strcpy(opName,op); strcpy(opCmd,c); opKind=kind; opRate=rate; opPending=true;
    operatorLog("OPERATOR_ACCEPTED",opId,opName,opCmd,"QUEUED","NONE");
  }
  void poll(uint32_t c,uint32_t when) {
    if (!ready || waiting || pollStep>=0 || opPending) {
      benchLog.print("node_id=shrimp-node04 sensor=PUMP_ATLAS_PMP event=POLL_SKIPPED_NOT_READY cycle=%lu",(unsigned long)c); return;
    }
    if (used || u.available() || millis()-lastRX<200) {event("POLL_SKIPPED_RX_BUSY"); return;}
    cycle=c; scheduled=when; ++seq; requested=millis(); waitUntil=requested;
    rawD[0]=rawPV[0]=rawTV[0]=0; motorV=total=NAN;
    // Re-send the setpoint after every (re)initialisation, and at most once a minute if the pump reports stopped.
    bool control=target>0 && (controlDue || (lastOn==0 && requested-lastControl>=60000));
    pollStep=control?0:1;
  }
  void service() {
    int budget=256;
    while (u.available() && budget-->0) {
      uint8_t b=u.read(); lastRX=millis();
      if (b=='\r') {onLine(); used=0; badLine=false;}
      else {
        if (b<32 || b>126) badLine=true;
        if (used<sizeof(line)-1) line[used++]=b; else badLine=true;
      }
    }
    uint32_t now=millis();
    if (used && now-lastRX>1800) {
      logHex("PARTIAL_LINE",line,used,false); used=0; badLine=false;
      if (waiting) fail("PARTIAL_LINE_TIMEOUT");
    }
    if (waiting) {if (now-started>=1800) fail("REPLY_TIMEOUT"); return;}
    if (opPending && ready && pollStep<0 && (int32_t)(now-waitUntil)>=0) {runOperator(); return;}
    if (pollStep>=0) {
      if ((int32_t)(now-waitUntil)<0) return;
      if (pollStep==0) {char c[24]; snprintf(c,sizeof(c),"DC,%.2f,*",target); lastControl=now; ++controls; send(c);}
      else if (pollStep==1) send("D,?");
      else if (pollStep==2) send("PV,?");
      else if (pollStep==3) send("TV,?");
      else report();
      return;
    }
    if (step==-1) {
      if ((int32_t)(now-retryAt)<0) return;
      // Factory default streams a reading every second; stop it, then drain for 2 s.
      event("STOP_CONTINUOUS_C0"); u.print("C,0\r"); step=-2; waitUntil=now+2000;
      return;
    }
    if (step==-2) {
      if ((int32_t)(now-waitUntil)<0 || used || now-lastRX<200) return;
      step=0;
    }
    if (ready || (int32_t)(now-waitUntil)<0) return;
    // Queries only. No calibration, factory reset, startup-dispense, baud or protocol writes.
    static const char *const init[]={"*OK,1","C,0","i","Status","Cal,?","Dstart,?","DC,?"};
    if (step>=int(sizeof(init)/sizeof(init[0]))) {
      ready=true;
      benchLog.print("node_id=shrimp-node04 boot_id=%s sensor=PUMP_ATLAS_PMP uptime_ms=%lu event=READY target_mL_min=%.2f calibration_reply=%s max_rate_reply=%s",
        bootID,(unsigned long)now,target,cal,maxRate);
      return;
    }
    send(init[step]);
  }
};
