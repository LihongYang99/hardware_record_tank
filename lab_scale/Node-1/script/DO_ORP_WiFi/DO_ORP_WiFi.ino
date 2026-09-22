// Bench-only, read-only. No calibration/configuration writes, MQTT or UTC sync.
// Independent buses: DO UART1 RX18/TX17; ORP UART2 RX16/TX15.
// DO: https://wiki.dfrobot.com/sen0681/docs/21674
// ORP: https://wiki.dfrobot.com/sen0709/docs/23382
#include <Arduino.h>
#include <WiFi.h>
#include <esp_system.h>
#include <math.h>
#include "arduino_secrets.h"
#include "Protocol.h"
#include "BenchChannel.h"

HardwareSerial doUART(1), orpUART(2);
const uint32_t POLL_INTERVAL_MS = 4000;
BenchChannel doChannel(doUART, "DO_SEN0681", 6, POLL_INTERVAL_MS);
BenchChannel orpChannel(orpUART, "ORP_SEN0709", 2, POLL_INTERVAL_MS);
uint32_t lastCycle = 0, cycleNumber = 0;
char bootID[17];
uint32_t lastWiFiPrint = 0, lastWiFiRetry = 0;

void printRaw(const uint8_t* p, size_t n) {
  for (size_t i = 0; i < n; ++i) Serial.printf("%02X", p[i]);
}

void reportChannel(BenchChannel& c) {
  Serial.printf("node_id=shrimp-node01 boot_id=%s sensor=%s seq=%lu "
                "request_uptime_ms=%lu rx_uptime_ms=",
                bootID, c.id, (unsigned long)c.seq, (unsigned long)c.started);
  if (c.length) Serial.printf("%lu", (unsigned long)c.lastByte);
  else Serial.print("NA");
  Serial.printf(" cycle=%lu scheduled_uptime_ms=%lu", (unsigned long)c.cycle,
                (unsigned long)c.scheduled);
  Serial.printf(" report_uptime_ms=%lu UTC=UNSYNCED raw=", (unsigned long)millis());
  printRaw(c.raw, c.length);
  if (c.dropped) {
    Serial.printf(" COMM=ERROR QC=COMMUNICATION_ERROR reason=RX_OVERFLOW dropped_bytes=%lu\n",
                  (unsigned long)c.dropped);
    return;
  }
  const char* error = frameError(c.raw, c.length, c.registers * 2);
  if (error) {
    Serial.printf(" COMM=ERROR QC=COMMUNICATION_ERROR reason=%s", error);
    if (strcmp(error, "MODBUS_EXCEPTION") == 0)
      Serial.printf(" exception_code=%u", c.raw[2]);
    Serial.println();
    return;
  }
  if (c.registers == 6) {
    const float saturation = floatBE(c.raw + 3) * 100.0f;
    const float oxygen = floatBE(c.raw + 7);
    const float temperature = floatBE(c.raw + 11);
    if (!isfinite(saturation) || !isfinite(oxygen) || !isfinite(temperature)) {
      Serial.println(" COMM=OK QC=SENSOR_FAULT reason=NONFINITE");
      return;
    }
    const bool validRange = oxygen >= 0 && oxygen <= 20 &&
        saturation >= 0 && saturation <= 200 && temperature >= 0 && temperature <= 40;
    Serial.printf(" DO_mg_L=%.3f saturation_pct=%.2f temperature_C=%.2f COMM=OK QC=%s\n",
                  oxygen, saturation, temperature, validRange ? "UNVALIDATED" : "OUT_OF_RANGE");
  } else {
    const int32_t orp = signedBE16(c.raw + 3);
    const float temperature = signedBE16(c.raw + 5) / 10.0f;
    const bool validRange = orp >= -1999 && orp <= 1999 && temperature >= 0 && temperature <= 60;
    Serial.printf(" ORP_mV=%ld temperature_C=%.1f COMM=OK QC=%s\n",
                  (long)orp, temperature, validRange ? "UNVALIDATED" : "OUT_OF_RANGE");
  }
}

void serviceSensor(BenchChannel& c, bool pollDue) {
  uint32_t now = millis();
  if (pollDue && c.waiting)
    Serial.printf("sensor=%s cycle=%lu QC=STALE reason=POLL_SKIPPED_BUSY\n",
                  c.id, (unsigned long)cycleNumber);
  if (!c.waiting) {
    // Drain at most one bounded chunk per loop; preserve late/unrequested bytes.
    int pending = c.uart.available();
    if (pending > 0) {
      if (pending > 128) pending = 128;
      Serial.printf("node_id=shrimp-node01 boot_id=%s sensor=%s uptime_ms=%lu UNSOLICITED_RAW=",
                    bootID, c.id, (unsigned long)now);
      while (pending-- > 0) Serial.printf("%02X", c.uart.read());
      Serial.println();
      c.lastPoll = now;
      if (pollDue)
        Serial.printf("sensor=%s cycle=%lu QC=COMMUNICATION_ERROR reason=POLL_SKIPPED_UNSOLICITED\n",
                      c.id, (unsigned long)cycleNumber);
      return;
    }
    if (!pollDue) return;
    uint8_t request[] = {1, 3, 0, 0, 0, c.registers, 0, 0};
    const uint16_t crc = modbusCRC(request, 6);
    request[6] = crc & 0xFF;
    request[7] = crc >> 8;
    c.length = 0;
    c.dropped = 0;
    c.started = c.lastPoll = now;
    c.cycle = cycleNumber;
    c.scheduled = lastCycle;
    ++c.seq;
    c.waiting = true;
    c.uart.write(request, sizeof(request));
  }
  int pending = c.uart.available();
  if (pending > 128) pending = 128;
  while (pending-- > 0) {
    const uint8_t b = c.uart.read();
    if (c.length < sizeof(c.raw)) c.raw[c.length++] = b;
    else {
      // Preserve overflow bytes separately and invalidate the whole response.
      Serial.printf("sensor=%s seq=%lu OVERFLOW_RAW=%02X\n", c.id, (unsigned long)c.seq, b);
      ++c.dropped;
    }
    c.lastByte = millis();
  }
  now = millis();
  if ((c.length && now - c.lastByte >= 30) || now - c.started >= 1000) {
    reportChannel(c);
    c.waiting = false;
  }
}

void serviceWiFi() {
  const uint32_t now = millis();
  if (now - lastWiFiPrint >= 5000) {
    lastWiFiPrint = now;
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print("[WiFi] Connected | IP=");
      Serial.println(WiFi.localIP());
    } else Serial.println("[WiFi] Not connected");
  }
  if (WiFi.status() != WL_CONNECTED && now - lastWiFiRetry >= 30000) {
    lastWiFiRetry = now;
    WiFi.reconnect();
  }
}

void setup() {
  Serial.begin(115200);
  doUART.begin(4800, SERIAL_8N1, 18, 17);
  orpUART.begin(4800, SERIAL_8N1, 16, 15);
  WiFi.setHostname("shrimp-node01");
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  snprintf(bootID, sizeof(bootID), "%08lx%08lx", (unsigned long)esp_random(), (unsigned long)esp_random());
  lastWiFiRetry = millis();
  lastCycle = millis();
}

void loop() {
  const uint32_t now = millis();
  const uint32_t ticks = (now - lastCycle) / POLL_INTERVAL_MS;
  const bool pollDue = ticks > 0;
  if (pollDue) {
    lastCycle += ticks * POLL_INTERVAL_MS;
    cycleNumber += ticks;
    if (ticks > 1)
      Serial.printf("QC=STALE reason=MISSED_POLL_CYCLES count=%lu\n", (unsigned long)(ticks - 1));
  }
  // One common schedule; separate UART transmissions, not hardware triggering.
  serviceSensor(doChannel, pollDue);
  serviceSensor(orpChannel, pollDue);
  // Network maintenance between transactions to reduce interference with replies.
  if (!doChannel.waiting && !orpChannel.waiting) serviceWiFi();
}
