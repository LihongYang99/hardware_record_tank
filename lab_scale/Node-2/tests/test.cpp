#include <cassert>
#include <iostream>
#include "Arduino.h"
#include "../script/Atlas_EC_pH_UART/BenchLog.h"
uint32_t fakeTime=0;FakeUSB Serial;BenchLog benchLog;char bootID[17]="test";
#include "../script/Atlas_EC_pH_UART/AtlasChannel.h"
void flush(){for(int i=0;i<1000;i++)benchLog.service();}
void advance(AtlasChannel &a,AtlasChannel &b,uint32_t ms){
  for(uint32_t i=0;i<ms;i+=10){fakeTime+=10;a.service();b.service();flush();}
}
int main(){
  assert(atlasIdentity("?I,EC,2.17",true));
  assert(atlasIdentity("?I,pH,2.17",false));
  assert(atlasIdentity("?i,EC,2.15",true));
  assert(atlasIdentity("?i,pH,2.0",false));
  assert(!atlasIdentity("?I,pH,2.17",true));
  assert(!atlasIdentity("?I,EC,2.17",false));
  assert(!atlasIdentity("?I,EC,",true));
  assert(!atlasIdentity("",true));
  double a,b;
  assert(atlasValues("35000.0,22.5",true,a,b)&&a==35000&&b==22.5);
  assert(atlasValues("8.123",false,a,b));
  for(auto s:{"","NaN","inf","0x12","8.0x","1e9","1,2"," "})assert(!atlasNumber(s,a));
  assert(!atlasValues("1,2,3",true,a,b));assert(!atlasValues("1,",true,a,b));
  HardwareSerial eu,pu;pu.ec=false;
  AtlasChannel ec(eu,"EC",true),ph(pu,"pH",false);
  ec.begin(18,17);ph.begin(16,15);
  advance(ec,ph,8000);assert(ec.ready&&ph.ready);
  ec.poll(2,8000);ph.poll(2,8000);advance(ec,ph,1000);
  assert(ec.seq==1&&ph.seq==1);
  assert(Serial.output.find("EC_uS_cm=35000.000 salinity_PSU=22.500")!=std::string::npos);
  assert(Serial.output.find("pH=8.123")!=std::string::npos);
  assert(Serial.output.find("QC=COMPENSATION_MISSING")!=std::string::npos);
  assert(Serial.output.find("calibration_reply=?CAL,0")!=std::string::npos);
  eu.silent=true;ec.poll(3,12000);ph.poll(3,12000);advance(ec,ph,2000);
  assert(!ec.ready&&ph.ready);assert(Serial.output.find("REPLY_TIMEOUT")!=std::string::npos);
  eu.silent=false;advance(ec,ph,23000);assert(ec.ready);
  // Reboot invalidates the setup rather than treating a later number as configured.
  eu.inject("*RS\r");advance(ec,ph,50);assert(!ec.ready);
  eu.wrongID=true;advance(ec,ph,22000);assert(!ec.ready);
  assert(Serial.output.find("WRONG_OR_MISSING_EZO_ID")!=std::string::npos);
  for(auto &c:eu.commands)assert(c!="Factory"&&c!="K,10"&&(c.find("Cal,")==std::string::npos || c=="Cal,?"));
  Serial.connected=false;for(int i=0;i<100;i++)benchLog.print("test");assert(benchLog.lost>0);
  std::cout<<"PASS: strict parsing, initialization, dual reads, independent timeout, recovery, reboot/ID checks, bounded USB queue\n";
}
