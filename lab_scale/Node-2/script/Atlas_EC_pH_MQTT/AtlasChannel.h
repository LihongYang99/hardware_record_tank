#pragma once
#include <Arduino.h>
#include "AtlasParse.h"
#include "BenchLog.h"
extern BenchLog benchLog;
extern char bootID[17];
// Each channel has its own UART and independent timeout/state machine.
class AtlasChannel {
  HardwareSerial &u; const char *name; bool ec;
  char line[128]={},data[128]={},cmd[24]={}; size_t used=0;
  uint32_t started=0,lastRX=0,waitUntil=0,retryAt=0;
  bool waiting=false,reading=false,haveData=false,ack=false,badLine=false;
  int step=-1;
  double kval=NAN,tc=NAN; char cal[32]="UNKNOWN";
  void event(const char *reason) {
    benchLog.print("node_id=shrimp-node02 boot_id=%s sensor=%s uptime_ms=%lu event=%s seq=%lu cycle=%lu",
      bootID,name,(unsigned long)millis(),reason,(unsigned long)seq,(unsigned long)cycle);
  }
  void fail(const char *reason) {
    if (reading) benchLog.print("node_id=shrimp-node02 boot_id=%s sensor=%s seq=%lu cycle=%lu request_uptime_ms=%lu UTC=UNSYNCED COMM=ERROR QC=COMMUNICATION_ERROR reason=%s",
      bootID,name,(unsigned long)seq,(unsigned long)cycle,(unsigned long)started,reason);
    else event(reason);
    waiting=false; reading=false; ready=false; step=-1; retryAt=millis()+15000;
  }
  void send(const char *s,bool measurement=false) {
    strncpy(cmd,s,sizeof(cmd)-1); haveData=false; ack=false; data[0]=0;
    waiting=true; reading=measurement; started=millis();
    if (measurement) ++seq;
    benchLog.print("node_id=shrimp-node02 boot_id=%s sensor=%s event=TX command=%s uptime_ms=%lu seq=%lu",
      bootID,name,s,(unsigned long)started,(unsigned long)seq);
    u.print(s); u.write('\r');
  }
  void finish() {
    if (reading) {
      double a=NAN,b=NAN;
      if (!atlasValues(data,ec,a,b)) {fail("UNEXPECTED_VALUE_FORMAT"); return;}
      const char *qc="COMPENSATION_MISSING";
      if (ec && (!isfinite(kval) || fabs(kval-10.0)>0.0001)) qc="CONFIGURATION_MISMATCH";
      else if (ec ? (a<0 || b<0 || b>42) : (a<0 || a>14)) qc="OUT_OF_RANGE";
      if (ec) benchLog.print("node_id=shrimp-node02 boot_id=%s sensor=%s seq=%lu cycle=%lu scheduled_uptime_ms=%lu request_uptime_ms=%lu rx_uptime_ms=%lu UTC=UNSYNCED EC_uS_cm=%.3f salinity_PSU=%.3f K=%.3f compensation_setting_C=%.2f calibration_reply=%s COMM=OK QC=%s validation=UNVALIDATED temp_source=NOT_VERIFIED",
        bootID,name,(unsigned long)seq,(unsigned long)cycle,(unsigned long)scheduled,(unsigned long)started,(unsigned long)sampleRX,a,b,kval,tc,cal,qc);
      else benchLog.print("node_id=shrimp-node02 boot_id=%s sensor=%s seq=%lu cycle=%lu scheduled_uptime_ms=%lu request_uptime_ms=%lu rx_uptime_ms=%lu UTC=UNSYNCED pH=%.3f compensation_setting_C=%.2f calibration_reply=%s COMM=OK QC=%s validation=UNVALIDATED temp_source=NOT_VERIFIED",
        bootID,name,(unsigned long)seq,(unsigned long)cycle,(unsigned long)scheduled,(unsigned long)started,(unsigned long)sampleRX,a,tc,cal,qc);
      reading=false;
    } else {
      if (!strcmp(cmd,"i")) {
        if (!atlasIdentity(data,ec)) {fail("WRONG_OR_MISSING_EZO_ID"); return;}
      } else if (!strcmp(cmd,"K,?")) {
        if (strncmp(data,"?K,",3) || !atlasNumber(data+3,kval)) {fail("BAD_K_REPLY"); return;}
      } else if (!strcmp(cmd,"T,?")) {
        if (strncmp(data,"?T,",3) || !atlasNumber(data+3,tc)) {fail("BAD_T_REPLY"); return;}
      } else if (!strcmp(cmd,"Cal,?")) {
        if ((strncmp(data,"?Cal,",5) && strncmp(data,"?CAL,",5)) || strlen(data)>=sizeof(cal)) {fail("BAD_CAL_REPLY"); return;}
        strcpy(cal,data);
      }
      ++step;
    }
    waiting=false; waitUntil=millis()+200;
  }
  void onLine() {
    // raw_hex includes CR terminator; preserve control/error lines as well as data.
    char hex[259]; const char *digits="0123456789ABCDEF";
    for(size_t i=0;i<used;++i) {uint8_t b=line[i];hex[2*i]=digits[b>>4];hex[2*i+1]=digits[b&15];}
    hex[2*used]='0';hex[2*used+1]='D';hex[2*used+2]=0;
    benchLog.print("node_id=shrimp-node02 boot_id=%s sensor=%s rx_uptime_ms=%lu seq=%lu event=RX raw_hex=%s",
      bootID,name,(unsigned long)lastRX,(unsigned long)seq,hex);
    if (badLine) {if(waiting) fail("INVALID_ASCII_OR_OVERLONG_LINE"); return;}
    line[used]=0;
    if (step<0) return; // startup/recovery drain, never interpret as a measurement
    if (!strcmp(line,"*RS") || !strcmp(line,"*RE") || !strcmp(line,"*UV") || !strcmp(line,"*OV") || !strcmp(line,"*ER")) {
      fail(line); return;
    }
    if (!waiting) {event("UNSOLICITED_LINE"); return;}
    if (!strcmp(line,"*OK")) ack=true;
    else if (used) {
      if (haveData) {fail("MULTIPLE_REPLY_LINES");return;}
      strcpy(data,line);haveData=true;sampleRX=lastRX;
    }
    bool needsData=reading || !strcmp(cmd,"i") || strchr(cmd,'?');
    if (ack && (!needsData || haveData)) finish();
  }
public:
  bool ready=false; uint32_t seq=0,cycle=0,scheduled=0,sampleRX=0;
  AtlasChannel(HardwareSerial &uart,const char *id,bool isEC):u(uart),name(id),ec(isEC){}
  void begin(int rx,int tx) {
    u.setRxBufferSize(1024);u.begin(9600,SERIAL_8N1,rx,tx);
    retryAt=millis()+2000; // board/EZO startup grace period
  }
  void poll(uint32_t c,uint32_t when) {
    if (!ready || waiting) {
      benchLog.print("sensor=%s event=POLL_SKIPPED_NOT_READY cycle=%lu",name,(unsigned long)c);return;
    }
    cycle=c;scheduled=when;
    if (used || u.available() || millis()-lastRX<200) {event("POLL_SKIPPED_RX_BUSY");return;}
    send("R",true);
  }
  void service() {
    int budget=256;
    while (u.available() && budget-->0) {
      uint8_t b=u.read();lastRX=millis();
      if (b=='\r') {onLine();used=0;badLine=false;}
      else {
        if (b<32 || b>126) badLine=true;
        if (used<sizeof(line)-1) line[used++]=b;
        else {
          // Expose dropped bytes rather than silently accepting a truncated number.
          benchLog.print("sensor=%s event=LINE_OVERFLOW byte_hex=%02X uptime_ms=%lu",name,b,(unsigned long)lastRX);
          badLine=true;
        }
      }
    }
    uint32_t now=millis();
    if (used && now-lastRX>1800) {
      // Incomplete line: preserve received bytes; do not parse as valid data.
      char h[255];for(size_t i=0;i<used;i++) snprintf(h+2*i,3,"%02X",(uint8_t)line[i]);
      benchLog.print("sensor=%s event=PARTIAL_LINE raw_hex=%s",name,h);
      used=0;badLine=false;if(waiting) fail("PARTIAL_LINE_TIMEOUT");
    }
    if (waiting) {if(now-started>=1800) fail("REPLY_TIMEOUT");return;}
    if (step==-1) {
      if ((int32_t)(now-retryAt)<0) return;
      // Stop factory continuous output, then drain for 2 seconds.
      event("STOP_CONTINUOUS_C0");u.print("C,0\r");step=-2;
      waitUntil=now+2000;retryAt=now+0x3FFFFFFF;
    }
    if (step==-2 && (int32_t)(now-waitUntil)>=0) {
      if(used || now-lastRX<200) return;
      step=0;
    }
    if (step<0 || ready || (int32_t)(now-waitUntil)<0) return;
    // Only output/response settings are changed. No calibration/K/temperature writes.
    const char *ecInit[]={"*OK,1","C,0","i","K,?","T,?","Cal,?","O,EC,1","O,TDS,0","O,S,1","O,SG,0"};
    const char *phInit[]={"*OK,1","C,0","i","T,?","Cal,?"};
    int total=ec?10:5;
    if(step>=total) {ready=true;event("READY");return;}
    send(ec?ecInit[step]:phInit[step]);
  }
};
