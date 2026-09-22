#pragma once
#include <Arduino.h>

struct BenchChannel {
  HardwareSerial& uart;
  const char* id;
  uint8_t registers;
  uint32_t interval;
  uint8_t raw[256] = {};
  size_t length = 0;
  uint32_t dropped = 0;
  uint32_t lastPoll = 0, started = 0, lastByte = 0, seq = 0;
  uint32_t cycle = 0, scheduled = 0;
  bool waiting = false;
  BenchChannel(HardwareSerial& u, const char* name, uint8_t count, uint32_t ms)
      : uart(u), id(name), registers(count), interval(ms) {}
};
