// Node 7 (shrimp-node07): aquarium heater on CH1 of a two-channel IoT AC power relay (heater plugged into the
// CH1 "normally OFF" outlet: no control signal = no heater power). ESP32 GPIO5 -> relay CH1 control input (+),
// ESP32 GND -> CH1 control input (-). The ESP32 never touches mains. The thermostat decision is made by the gateway
// (jetson_web/heater_ctl.py) from water temperature; this node only obeys HEAT,ON / HEAT,OFF and switches the relay
// OFF by itself when no HEAT,ON arrived for HOLD_MS (gateway, network or broker failure), at boot and on a wrong board.
// Telemetry.h and BenchLog.h are byte-identical to pump-node-1. UTC remains UNSYNCED.
#include <Arduino.h>
#include <WiFi.h>
#include <esp_system.h>
#include <esp_mac.h>
#include "arduino_secrets.h"
#define TELEMETRY_NODE "shrimp-node07"
#define TELEMETRY_FIRMWARE "node07-heater-mqtt-0.1"
#define TELEMETRY_COMMAND_TOPIC "shrimp/lab/" TELEMETRY_NODE "/cmd"
#include "Telemetry.h"
Telemetry telemetry;
#include "BenchLog.h"
BenchLog benchLog;
#include "HeaterLogic.h"
// Factory MAC of the Node 7 ESP32, read with esptool before flashing. All zeros never drives the relay.
const uint8_t NODE_MAC[6]={0,0,0,0,0,0};
const int RELAY_CH1=5;                         // not a strapping pin; HIGH = relay CH1 energised = heater outlet on
const uint32_t POLL_MS=4000, HOLD_MS=60000;    // gateway repeats HEAT,ON every 20 s; 60 s without it -> OFF
bool correctBoard=false, relayOn=false;
uint32_t lastOn=0, lastCycle=0, cycle=0, seq=0, lastHealth=0, lastWiFiPrint=0, lastWiFiRetry=0, commands=0, rejected=0;
char bootID[17];

void setRelay(bool on, const char *reason) {
  digitalWrite(RELAY_CH1, on ? HIGH : LOW);
  if (on != relayOn)
    benchLog.print("node_id=" TELEMETRY_NODE " boot_id=%s sensor=HEATER_RELAY event=RELAY_%s reason=%s uptime_ms=%lu",
                   bootID, on ? "ON" : "OFF", reason, (unsigned long)millis());
  relayOn = on;
}

void setup() {
  pinMode(RELAY_CH1, OUTPUT); digitalWrite(RELAY_CH1, LOW);  // first thing: heater off
  Serial.begin(115200);
#if !ARDUINO_USB_CDC_ON_BOOT || !ARDUINO_USB_MODE
#error Select USB CDC On Boot enabled and USB Mode Hardware CDC and JTAG.
#endif
  Serial.setTxTimeoutMs(0);
  WiFi.mode(WIFI_STA);
  const uint8_t unset[6]={};
  uint8_t mac[6]={};
  correctBoard=esp_efuse_mac_get_default(mac)==ESP_OK && memcmp(NODE_MAC,unset,6) && !memcmp(mac,NODE_MAC,6);
  if (!correctBoard) return;
  snprintf(bootID,sizeof(bootID),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
  if (!telemetry.begin(bootID)) { correctBoard=false; return; }
  WiFi.setHostname(TELEMETRY_NODE);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  lastWiFiRetry=lastCycle=millis();
  benchLog.print("node_id=" TELEMETRY_NODE " boot_id=%s event=BOOT relay=OFF hold_ms=%lu UTC=UNSYNCED transport=MQTT",bootID,(unsigned long)HOLD_MS);
}

void loop() {
  if (!correctBoard) {
    digitalWrite(RELAY_CH1, LOW);
    if (millis()-lastHealth>=5000) { lastHealth=millis(); Serial.println("node_id=" TELEMETRY_NODE " event=WRONG_BOARD relay=OFF"); }
    delay(100); return;
  }
  char text[128];
  while (telemetry.nextCommand(text,sizeof(text))) {
    const int c=heaterCommand(text);
    if (c<0) { ++rejected; benchLog.print("node_id=" TELEMETRY_NODE " boot_id=%s sensor=HEATER_RELAY event=COMMAND_REJECTED payload_len=%u",bootID,(unsigned)strlen(text)); continue; }
    ++commands;
    if (c) lastOn=millis();
    setRelay(c==1, c ? "COMMAND_ON" : "COMMAND_OFF");
  }
  const uint32_t now=millis();
  if (relayOn && heaterExpired(now,lastOn,HOLD_MS)) setRelay(false,"NO_ON_REFRESH");
  if (now-lastCycle>=POLL_MS) {
    lastCycle+=POLL_MS*((now-lastCycle)/POLL_MS); ++cycle;
    benchLog.print("node_id=" TELEMETRY_NODE " boot_id=%s sensor=HEATER_RELAY seq=%lu cycle=%lu request_uptime_ms=%lu UTC=UNSYNCED relay_on=%d gpio=%d on_command_age_s=%s COMM=OK QC=UNVALIDATED",
      bootID,(unsigned long)++seq,(unsigned long)cycle,(unsigned long)now,relayOn,digitalRead(RELAY_CH1),
      relayOn ? String((now-lastOn)/1000).c_str() : "NA");
  }
  if (now-lastWiFiPrint>=5000) {
    lastWiFiPrint=now;
    if (WiFi.status()==WL_CONNECTED) benchLog.print("[WiFi] Connected | IP=%s | node_id=" TELEMETRY_NODE,WiFi.localIP().toString().c_str());
    else benchLog.print("[WiFi] Not connected | status=%d | node_id=" TELEMETRY_NODE,WiFi.status());
  }
  if (WiFi.status()!=WL_CONNECTED && now-lastWiFiRetry>=30000) { lastWiFiRetry=now; WiFi.reconnect(); }
  if (now-lastHealth>=10000) {
    lastHealth=now;
    benchLog.print("node_id=" TELEMETRY_NODE " boot_id=%s event=HEALTH uptime_ms=%lu relay_on=%d commands=%lu rejected=%lu command_lost=%lu UTC=UNSYNCED mqtt_lost=%lu usb_lost=%lu format_lost=%lu line_too_long=%lu queued=%u",
      bootID,(unsigned long)now,relayOn,(unsigned long)commands,(unsigned long)rejected,(unsigned long)telemetry.commandLost,
      (unsigned long)telemetry.mqttLost,(unsigned long)telemetry.usbLost,(unsigned long)telemetry.formatLost,(unsigned long)benchLog.lost,telemetry.queued());
  }
  benchLog.service();
  delay(1);
}
