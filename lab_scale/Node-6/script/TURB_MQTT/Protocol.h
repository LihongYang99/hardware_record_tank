#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

inline uint16_t modbusCRC(const uint8_t* p, size_t n) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < n; ++i) {
    crc ^= p[i];
    for (int b = 0; b < 8; ++b)
      crc = (crc & 1) ? (crc >> 1) ^ 0xA001 : crc >> 1;
  }
  return crc;
}
inline int32_t signedBE16(const uint8_t* p) {
  const uint32_t u = (uint32_t(p[0]) << 8) | p[1];
  return u >= 0x8000 ? int32_t(u) - 65536 : int32_t(u);
}
inline float floatBE(const uint8_t* p) {
  const uint32_t bits = (uint32_t(p[0]) << 24) |
      (uint32_t(p[1]) << 16) | (uint32_t(p[2]) << 8) | p[3];
  float f;
  memcpy(&f, &bits, sizeof(f));
  return f;
}
inline const char* frameError(const uint8_t* p, size_t n, uint8_t dataBytes) {
  if (!n) return "TIMEOUT";
  if (n < 5) return "SHORT_FRAME";
  if (modbusCRC(p, n - 2) != (p[n-2] | (uint16_t(p[n-1]) << 8)))
    return "CRC_ERROR";
  if (p[0] != 1) return "WRONG_ADDRESS";
  if (p[1] == 0x83 && n == 5) return "MODBUS_EXCEPTION";
  if (n != size_t(dataBytes + 5) || p[1] != 3 || p[2] != dataBytes)
    return "UNEXPECTED_FRAME";
  return nullptr;
}
