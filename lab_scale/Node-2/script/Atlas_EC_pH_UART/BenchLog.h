#pragma once
#include <Arduino.h>
#include <stdarg.h>
// Bounded USB logging. Acquisition does not wait for a closed Serial Monitor.
// RAM queue is NOT durable storage. Explicit counter exposes overflow.
class BenchLog {
  char q[32][768]; uint16_t sizes[32]={};
  unsigned head=0,tail=0,count=0,offset=0;
public:
  uint32_t lost=0;
  void print(const char *fmt,...) {
    if (count==32) {++lost; return;}
    va_list ap; va_start(ap,fmt);
    int n=vsnprintf(q[tail],sizeof(q[tail]),fmt,ap); va_end(ap);
    if (n<0 || n>=int(sizeof(q[tail])-1)) {++lost; return;}
    q[tail][n++]='\n'; sizes[tail]=n;
    tail=(tail+1)%32; ++count;
  }
  void service() {
    if (!Serial || !count) return;
    int room=Serial.availableForWrite(); if (room<=0) return;
    size_t n=sizes[head]-offset;
    if (n>size_t(room)) n=room; if (n>64) n=64;
    offset+=Serial.write((const uint8_t*)q[head]+offset,n);
    if (offset==sizes[head]) {offset=0; head=(head+1)%32; --count;}
  }
};
