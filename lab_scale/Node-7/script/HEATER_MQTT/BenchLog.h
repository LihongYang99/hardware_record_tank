#pragma once
#include <Arduino.h>
#include <stdarg.h>
// Same print()/service() interface as the USB-only BenchLog, so AtlasChannel.h is unchanged.
// Every line goes to Telemetry: bounded MQTT queue (application ACK) + bounded USB queue.
class BenchLog {
public:
  uint32_t lost=0; // lines longer than the original 767-character limit
  void print(const char *fmt,...) {
    char line[768];
    va_list ap; va_start(ap,fmt);
    int n=vsnprintf(line,sizeof(line),fmt,ap); va_end(ap);
    if (n<0 || n>=int(sizeof(line)-1)) {++lost; return;}
    telemetry.write(reinterpret_cast<const uint8_t*>(line),n);
    telemetry.write('\n');
  }
  void service() { telemetry.serviceUSB(); }
};
