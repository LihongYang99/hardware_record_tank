#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <string>
#include <deque>
#include <vector>
extern uint32_t fakeTime; extern int fakeINT;
inline uint32_t millis(){return fakeTime;}
#define INPUT_PULLDOWN 9
#define SERIAL_8N1 0
inline void pinMode(int,int){}
inline int digitalRead(int){return fakeINT;}
// Fake EZO-PMP giving the UART replies documented in the Atlas EZO-PMP datasheet.
class HardwareSerial {
public:
  bool silent=false,running=false,tooFast=false,noMotor=false,wrongID=false,intStuckLow=false,calibrated=false; double motorV=12.1;
  std::string command; std::deque<uint8_t> rx; std::vector<std::string> commands;
  void setRxBufferSize(size_t){}
  void begin(int,int,int,int){}
  int available(){return (int)rx.size();}
  int read(){uint8_t b=rx.front();rx.pop_front();return b;}
  void inject(const std::string&s){for(char b:s)rx.push_back((uint8_t)b);}
  void print(const char*s){while(*s)write((uint8_t)*s++);}
  size_t write(uint8_t b){
    if(b!='\r'){command+=char(b);return 1;}
    std::string c=command;command.clear();commands.push_back(c);
    if(silent)return 1;
    char s[48];
    if(c=="i")inject(wrongID?"?I,pH,2.17\r":"?i,PMP,1.1\r");
    else if(c=="Status")inject("?Status,P,3.30\r");
    else if(c=="Cal,?")inject(calibrated?"?CAL,1\r":"?Cal,0\r");
    else if(c=="Dstart,?")inject("?Dstart,0\r");
    else if(c=="DC,?")inject(calibrated?"?MAXRATE,60.00\r":"?MAXRATE,105.00\r");
    else if(c.rfind("DC,",0)==0){if(noMotor){inject("*UV,PUMPPWR,0.00\r*ER\r");return 1;}if(tooFast){inject("*TOOFAST\r*ER\r");return 1;}running=true;}
    else if(c=="X"){running=false;fakeINT=0;inject("*DONE,3.50\r");return 1;}
    else if(c.rfind("D,",0)==0&&c!="D,?")running=true;
    else if(c.rfind("Cal,",0)==0&&c!="Cal,?")calibrated=c!="Cal,clear";
    else if(c=="D,?")inject(running?"?D,*,1\r":"?D,0.00,0\r");
    else if(c=="PV,?"){snprintf(s,sizeof(s),"?PV,%.2f\r",motorV);inject(s);}
    else if(c=="TV,?")inject("?TV,5.25\r");
    fakeINT=running&&!intStuckLow;
    inject("*OK\r");return 1;
  }
};
