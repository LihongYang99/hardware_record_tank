#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string>
#include <deque>
#include <vector>
extern uint32_t fakeTime;
inline uint32_t millis(){return fakeTime;}
struct FakeUSB {
  std::string output; bool connected=true;
  operator bool()const{return connected;}
  int availableForWrite(){return connected?256:0;}
  size_t write(const uint8_t*p,size_t n){output.append((const char*)p,n);return n;}
};
extern FakeUSB Serial;
class HardwareSerial {
public:
  bool ec=true,silent=false,wrongID=false;std::string command;
  std::deque<uint8_t> rx;std::vector<std::string> commands;
  void setRxBufferSize(size_t){}
  void begin(int,int,int,int){}
  int available(){return rx.size();}
  int read(){auto b=rx.front();rx.pop_front();return b;}
  void inject(const std::string&s){for(auto b:s)rx.push_back(b);}
  void print(const char*s){while(*s)write(*s++);}
  size_t write(uint8_t b){
    if(b!='\r'){command+=char(b);return 1;}
    std::string c=command;command.clear();commands.push_back(c);
    if(silent)return 1;
    if(c=="i")inject(wrongID?"?I,DO,1.0\r":ec?"?I,EC,2.17\r":"?I,pH,2.17\r");
    else if(c=="K,?")inject("?K,10\r");
    else if(c=="T,?")inject("?T,25.00\r");
    else if(c=="Cal,?")inject("?CAL,0\r");
    else if(c=="R")inject(ec?"35000.0,22.50\r":"8.123\r");
    inject("*OK\r");return 1;
  }
};
#define SERIAL_8N1 0
