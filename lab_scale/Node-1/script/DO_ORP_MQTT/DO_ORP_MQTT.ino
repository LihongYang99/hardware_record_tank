// Lab MQTT variant. Sensor requests unchanged; UTC remains explicitly UNSYNCED.
// Independent buses: DO UART1 RX18/TX17; ORP UART2 RX16/TX15.
// DO: https://wiki.dfrobot.com/sen0681/docs/21674
// ORP: https://wiki.dfrobot.com/sen0709/docs/23382
#include <Arduino.h>
#include <WiFi.h>
#include <esp_system.h>
#include <esp_mac.h>
#include <math.h>
#include "arduino_secrets.h"
#include "Protocol.h"
#include "BenchChannel.h"
#include "Telemetry.h"
Telemetry telemetry;
bool correctBoard=false;
uint32_t lastHealth=0;

HardwareSerial doUART(1), orpUART(2);
const uint32_t POLL_INTERVAL_MS = 4000;
BenchChannel doChannel(doUART, "DO_SEN0681", 6, POLL_INTERVAL_MS);
BenchChannel orpChannel(orpUART, "ORP_SEN0709", 2, POLL_INTERVAL_MS);
uint32_t lastCycle = 0, cycleNumber = 0;
char bootID[17];
uint32_t lastWiFiPrint = 0, lastWiFiRetry = 0;

void printRaw(const uint8_t* p, size_t n) {
  for (size_t i = 0; i < n; ++i) telemetry.printf("%02X", p[i]);
}

void reportChannel(BenchChannel& c) {
  telemetry.printf("node_id=shrimp-node01 boot_id=%s sensor=%s seq=%lu "
                "request_uptime_ms=%lu rx_uptime_ms=",
                bootID, c.id, (unsigned long)c.seq, (unsigned long)c.started);
  if (c.length) telemetry.printf("%lu", (unsigned long)c.lastByte);
  else telemetry.print("NA");
  telemetry.printf(" cycle=%lu scheduled_uptime_ms=%lu", (unsigned long)c.cycle,
                (unsigned long)c.scheduled);
  telemetry.printf(" report_uptime_ms=%lu UTC=UNSYNCED raw=", (unsigned long)millis());
  printRaw(c.raw, c.length);
  if (c.dropped) {
    telemetry.printf(" COMM=ERROR QC=COMMUNICATION_ERROR reason=RX_OVERFLOW dropped_bytes=%lu\n",
                  (unsigned long)c.dropped);
    return;
  }
  const char* error = frameError(c.raw, c.length, c.registers * 2);
  if (error) {
    telemetry.printf(" COMM=ERROR QC=COMMUNICATION_ERROR reason=%s", error);
    if (strcmp(error, "MODBUS_EXCEPTION") == 0)
      telemetry.printf(" exception_code=%u", c.raw[2]);
    telemetry.println();
    return;
  }
  if (c.registers == 6) {
    const float saturation = floatBE(c.raw + 3) * 100.0f;
    const float oxygen = floatBE(c.raw + 7);
    const float temperature = floatBE(c.raw + 11);
    if (!isfinite(saturation) || !isfinite(oxygen) || !isfinite(temperature)) {
      telemetry.println(" COMM=OK QC=SENSOR_FAULT reason=NONFINITE");
      return;
    }
    const bool validRange = oxygen >= 0 && oxygen <= 20 &&
        saturation >= 0 && saturation <= 200 && temperature >= 0 && temperature <= 40;
    telemetry.printf(" DO_mg_L=%.3f saturation_pct=%.2f temperature_C=%.2f COMM=OK QC=%s\n",
                  oxygen, saturation, temperature, validRange ? "UNVALIDATED" : "OUT_OF_RANGE");
  } else {
    const int32_t orp = signedBE16(c.raw + 3);
    const float temperature = signedBE16(c.raw + 5) / 10.0f;
    const bool validRange = orp >= -1999 && orp <= 1999 && temperature >= 0 && temperature <= 60;
    telemetry.printf(" ORP_mV=%ld temperature_C=%.1f COMM=OK QC=%s\n",
                  (long)orp, temperature, validRange ? "UNVALIDATED" : "OUT_OF_RANGE");
  }
}

void serviceSensor(BenchChannel& c, bool pollDue) {
  uint32_t now = millis();
  if (pollDue && c.waiting)
    telemetry.printf("sensor=%s cycle=%lu QC=STALE reason=POLL_SKIPPED_BUSY\n",
                  c.id, (unsigned long)cycleNumber);
  if (!c.waiting) {
    // Drain at most one bounded chunk per loop; preserve late/unrequested bytes.
    int pending = c.uart.available();
    if (pending > 0) {
      if (pending > 128) pending = 128;
      telemetry.printf("node_id=shrimp-node01 boot_id=%s sensor=%s uptime_ms=%lu UNSOLICITED_RAW=",
                    bootID, c.id, (unsigned long)now);
      while (pending-- > 0) telemetry.printf("%02X", c.uart.read());
      telemetry.println();
      c.lastPoll = now;
      if (pollDue)
        telemetry.printf("sensor=%s cycle=%lu QC=COMMUNICATION_ERROR reason=POLL_SKIPPED_UNSOLICITED\n",
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
      telemetry.printf("sensor=%s seq=%lu OVERFLOW_RAW=%02X\n", c.id, (unsigned long)c.seq, b);
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
      telemetry.print("[WiFi] Connected | IP=");
      telemetry.println(WiFi.localIP());
    } else telemetry.println("[WiFi] Not connected");
  }
  if (WiFi.status() != WL_CONNECTED && now - lastWiFiRetry >= 30000) {
    lastWiFiRetry = now;
    WiFi.reconnect();
  }
}

void setup() {
  Serial.begin(115200);
#if !ARDUINO_USB_CDC_ON_BOOT || !ARDUINO_USB_MODE
#error Select USB CDC On Boot enabled and USB Mode Hardware CDC and JTAG.
#endif
  Serial.setTxTimeoutMs(0);
  WiFi.mode(WIFI_STA);
  // Factory base MAC from eFuse; WiFi.macAddress() can be empty before the netif is up.
  const uint8_t node1Mac[6]={0x44,0xB1,0x76,0xCE,0xD1,0xA8};
  uint8_t mac[6]={};
  correctBoard=esp_efuse_mac_get_default(mac)==ESP_OK && memcmp(mac,node1Mac,6)==0;
  if(!correctBoard) return; // Never run Node 1 sensor traffic on another board.
  snprintf(bootID,sizeof(bootID),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
  if(!telemetry.begin(bootID)) { correctBoard=false; return; }
  doUART.begin(4800, SERIAL_8N1, 18, 17);
  orpUART.begin(4800, SERIAL_8N1, 16, 15);
  WiFi.setHostname("shrimp-node01");
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lastWiFiRetry=millis(); lastCycle=millis();
  telemetry.printf("node_id=shrimp-node01 boot_id=%s event=BOOT UTC=UNSYNCED transport=MQTT mqtt_lost=0\n",bootID);
}

void loop() {
  if(!correctBoard) {
    // Direct, non-blocking notice so a wrong board is never silent.
    if(millis()-lastHealth>=5000) { lastHealth=millis(); Serial.println("node_id=shrimp-node01 event=WRONG_BOARD sensors=DISABLED"); }
    delay(100); return;
  }
  const uint32_t now = millis();
  const uint32_t ticks = (now - lastCycle) / POLL_INTERVAL_MS;
  const bool pollDue = ticks > 0;
  if (pollDue) {
    lastCycle += ticks * POLL_INTERVAL_MS;
    cycleNumber += ticks;
    if (ticks > 1)
      telemetry.printf("QC=STALE reason=MISSED_POLL_CYCLES count=%lu\n", (unsigned long)(ticks - 1));
  }
  // One common schedule; separate UART transmissions, not hardware triggering.
  serviceSensor(doChannel, pollDue);
  serviceSensor(orpChannel, pollDue);
  // Network maintenance between transactions to reduce interference with replies.
  if (!doChannel.waiting && !orpChannel.waiting) serviceWiFi();
  if(now-lastHealth>=10000) {
    lastHealth=now;
    telemetry.printf("node_id=shrimp-node01 boot_id=%s event=HEALTH uptime_ms=%lu UTC=UNSYNCED mqtt_lost=%lu usb_lost=%lu format_lost=%lu queued=%u\n",
      bootID,(unsigned long)now,(unsigned long)telemetry.mqttLost,(unsigned long)telemetry.usbLost,
      (unsigned long)telemetry.formatLost,telemetry.queued());
  }
  telemetry.serviceUSB();
  delay(1); // Yield to the network/idle task; never wait on network in acquisition.

}
