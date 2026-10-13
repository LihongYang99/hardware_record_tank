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
  Serial.connected=true;

  // Operator payload grammar and calibration whitelist (ezo_cal.py builds the same commands).
  char id[21],op[25],cmd[32];bool isEC=false;
  assert(atlasOperatorPayload("id=17 operator=web-li cmd=EC:Cal,low,12880",id,op,isEC,cmd)&&isEC&&!strcmp(id,"17")&&!strcmp(op,"web-li")&&!strcmp(cmd,"Cal,low,12880"));
  assert(atlasOperatorPayload("id=18 operator=li cmd=PH:Cal,mid,7.00",id,op,isEC,cmd)&&!isEC&&!strcmp(cmd,"Cal,mid,7.00"));
  for(auto s:{"cmd=EC:K,10","id=1 operator=a cmd=K,10","id=1 operator=a cmd=DO:K,10","id=1 operator=a b cmd=EC:K,10","id=1 operator=a cmd=EC:",
              "id=1 operator=a cmd=EC:Cal, 5","id=1 operator=a cmd=EC:A=B","id=x operator=a cmd=EC:K,10","id=1 operator=a cmd=EC:Cal,high,1234567890123456789012345678"})
    assert(!atlasOperatorPayload(s,id,op,isEC,cmd));
  for(auto c:{"K,10","K,?","Cal,dry","Cal,low,12880","Cal,high,150000","Cal,12880","Cal,clear","Cal,?","T,?","Cal,low,10","Cal,high,500000"})assert(atlasOperatorCommand(c,true));
  for(auto c:{"Cal,mid,7.00","Cal,low,4.00","Cal,high,10.00","Cal,low,4.01","Cal,high,10.01","Cal,clear","Cal,?","Slope,?","T,?"})assert(atlasOperatorCommand(c,false));
  for(auto c:{"K,1","K,0.1","K,10.5","Cal,mid,7.00","Cal,low,5","Cal,high,600000","Cal,-5","Cal,1e4","Cal,low,","Slope,?","Factory","T,22.5","O,EC,0","Baud,38400","I2C,100","Plock,1","Sleep","Name,x","Cal,dry,1"})assert(!atlasOperatorCommand(c,true));
  for(auto c:{"Cal,7.00","Cal,dry","Cal,mid,8","Cal,low,6.5","Cal,high,7.9","Cal,high,14","K,10","K,?","Cal,mid,+7","Factory","T,25"})assert(!atlasOperatorCommand(c,false));

  // Live channels: K,10 and a full calibration; each command is one UART exchange between readings.
  HardwareSerial e2,p2;p2.ec=false;e2.k="1.00";
  AtlasChannel ec2(e2,"EC_ATLAS_EZO",true),ph2(p2,"PH_ATLAS_EZO",false);
  ec2.begin(18,17);ph2.begin(16,15);advance(ec2,ph2,8000);assert(ec2.ready&&ph2.ready);
  size_t startup=e2.commands.size();
  ec2.poll(2,fakeTime);advance(ec2,ph2,1000);
  assert(Serial.output.find("sensor=EC_ATLAS_EZO seq=1 ")!=std::string::npos&&Serial.output.find("K=1.000")!=std::string::npos);
  ec2.submit("1","li","K,10");advance(ec2,ph2,500);
  assert(Serial.output.find("event=OPERATOR_DONE cmd_id=1 operator=li command=K,10 result=OK reply=NONE")!=std::string::npos);
  // A change re-runs startup (K, T, Cal re-read) before the next reading is labelled.
  assert(!ec2.ready);advance(ec2,ph2,8000);assert(ec2.ready);
  ec2.poll(3,fakeTime);advance(ec2,ph2,1000);
  assert(Serial.output.find("K=10.000 compensation_setting_C=25.00 calibration_reply=?CAL,0 COMM=OK QC=COMPENSATION_MISSING")!=std::string::npos);
  ec2.submit("2","li","Cal,dry");advance(ec2,ph2,8000);
  ec2.submit("3","li","Cal,low,12880");advance(ec2,ph2,8000);
  ec2.submit("4","li","Cal,high,150000");advance(ec2,ph2,8000);
  ec2.submit("5","li","Cal,?");advance(ec2,ph2,500);
  assert(Serial.output.find("cmd_id=5 operator=li command=Cal,? result=OK reply=?CAL,2")!=std::string::npos&&ec2.ready);
  ph2.submit("6","li","Cal,mid,7.00");advance(ec2,ph2,8000);
  ph2.submit("7","li","Slope,?");advance(ec2,ph2,500);
  assert(Serial.output.find("command=Slope,? result=OK reply=?Slope,99.7,100.3,-0.89")!=std::string::npos);
  ph2.poll(9,fakeTime);advance(ec2,ph2,1000);
  assert(Serial.output.find("pH=8.123 compensation_setting_C=25.00 calibration_reply=?CAL,1")!=std::string::npos);
  // The EZO refusing a command (*ER) ends that command only; the channel stays ready and keeps reading.
  e2.refuse=true;ec2.submit("8","li","Cal,low,12880");advance(ec2,ph2,500);e2.refuse=false;
  assert(Serial.output.find("cmd_id=8 operator=li command=Cal,low,12880 result=ER")!=std::string::npos&&ec2.ready);
  // Refusals: not whitelisted, other channel's command, duplicate id, busy, not ready.
  ec2.submit("9","li","Factory");ec2.submit("10","li","Cal,mid,7.00");ec2.submit("9","li","K,?");flush();
  assert(Serial.output.find("cmd_id=9 operator=li command=Factory result=NOT_ALLOWED")!=std::string::npos);
  assert(Serial.output.find("cmd_id=10 operator=li command=Cal,mid,7.00 result=NOT_ALLOWED")!=std::string::npos);
  assert(Serial.output.find("cmd_id=9 operator=li command=K,? result=DUPLICATE_ID")!=std::string::npos);
  ec2.submit("11","li","K,?");ec2.submit("12","li","Cal,?");flush();
  assert(Serial.output.find("cmd_id=12 operator=li command=Cal,? result=ANOTHER_COMMAND_PENDING")!=std::string::npos);
  // An EZO reset cancels the queued/running command instead of running it late.
  e2.inject("*RS\r");advance(ec2,ph2,50);
  assert(Serial.output.find("cmd_id=11 operator=li command=K,? result=*RS")!=std::string::npos&&!ec2.ready);
  ec2.submit("13","li","K,?");flush();assert(Serial.output.find("cmd_id=13 operator=li command=K,? result=SENSOR_NOT_READY")!=std::string::npos);
  // No reply to an operator command: timeout, channel re-initialises, never a stored zero.
  advance(ec2,ph2,20000);assert(ec2.ready);
  e2.silent=true;ec2.submit("14","li","Cal,?");advance(ec2,ph2,3500);
  assert(Serial.output.find("cmd_id=14 operator=li command=Cal,? result=REPLY_TIMEOUT")!=std::string::npos&&!ec2.ready);
  e2.silent=false;
  // Only startup commands, R, and the whitelisted operator commands ever reached the EZOs.
  for(size_t i=startup;i<e2.commands.size();++i){auto&c=e2.commands[i];assert(c=="R"||c=="C,0"||c=="*OK,1"||c=="i"||c.rfind("O,",0)==0||atlasOperatorCommand(c.c_str(),true));}
  for(auto&c:p2.commands)assert(c=="R"||c=="C,0"||c=="*OK,1"||c=="i"||atlasOperatorCommand(c.c_str(),false));
  std::cout<<"PASS: strict parsing, initialization, dual reads, independent timeout, recovery, reboot/ID checks, bounded USB queue, operator calibration whitelist, K,10, EC 3-point / pH mid calibration, *ER, dedupe, busy, cancel on reset, operator timeout\n";
}
