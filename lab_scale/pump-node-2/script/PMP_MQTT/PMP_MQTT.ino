// pump-node-2 (overall Node 5, 泵 2). Same hardware, wiring and code as pump-node-1; only this file differs.
// UART1 9600 8N1: GPIO18 RX <- pump TX (green), GPIO17 TX -> pump RX (white). Pump INT (blue) -> GPIO4.
// Pump VCC (red) must be the ESP32 3V3 pin: at 5 V the pump TX would drive 5 V into GPIO18.
// The 12 V motor supply goes only to the pump's own power input, never to the ESP32. UTC remains UNSYNCED.
// BenchLog.h is a byte-identical copy from Node-2 Atlas_EC_pH_MQTT; Telemetry.h is that copy plus the
// optional command topic. Operator commands come only from pump_ctl.py (MQTT account pump-operator).
#include <Arduino.h>
#include <WiFi.h>
#include <Preferences.h>
#include <esp_system.h>
#include <esp_mac.h>
#include "arduino_secrets.h"
#define TELEMETRY_NODE "shrimp-node05"
#define PUMP_SENSOR "PUMP2_ATLAS_PMP"
#define TELEMETRY_FIRMWARE "node05-pump-mqtt-0.2"
#define TELEMETRY_COMMAND_TOPIC "shrimp/lab/" TELEMETRY_NODE "/cmd"
#include "Telemetry.h"
Telemetry telemetry;
#include "BenchLog.h"
BenchLog benchLog;
char bootID[17];
#include "PumpChannel.h"
// Setpoint when no operator setpoint was ever saved: 0 = the pump stays off until an operator starts it.
// An operator's last setpoint (DC,<rate>,* start, 0 after stop/dispense) is kept in NVS and restored on boot;
// a non-zero setpoint is re-sent after every pump reset. The motor only turns while its 12 V supply is connected.
const double PUMP_DEFAULT_ML_MIN=0.0;
// Factory MAC of the pump-node ESP32, read with esptool before flashing. All zeros never runs the pump.
const uint8_t NODE_MAC[6]={0x7C,0x4F,0xAD,0xB5,0x1C,0xD4}; // esptool flash-id, 2026-09-29
const int PUMP_RX=18, PUMP_TX=17, PUMP_INT=4;
HardwareSerial pumpUART(1);
PumpChannel pump(pumpUART,PUMP_INT,PUMP_DEFAULT_ML_MIN);
Preferences prefs;
const uint32_t POLL_MS=4000; // same cadence as Node 1 / Node 2
uint32_t lastCycle=0,cycle=0,lastHealth=0,lastRetry=0,lastWiFiPrint=0;
int previousWiFi=-999;
bool correctBoard=false;
uint8_t boardMac[6]={};
void setup() {
  Serial.begin(115200);
#if !ARDUINO_USB_CDC_ON_BOOT || !ARDUINO_USB_MODE
#error Select USB CDC On Boot enabled and USB Mode Hardware CDC and JTAG.
#endif
  Serial.setTxTimeoutMs(0);
  const uint8_t unset[6]={};
  correctBoard=esp_efuse_mac_get_default(boardMac)==ESP_OK && memcmp(NODE_MAC,unset,6) && !memcmp(boardMac,NODE_MAC,6);
  if(!correctBoard) return;
  snprintf(bootID,sizeof(bootID),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
  if(!telemetry.begin(bootID)) { correctBoard=false; return; }
  prefs.begin("pump",false);
  const bool saved=prefs.isKey("target");
  if(saved) pump.target=prefs.getDouble("target",PUMP_DEFAULT_ML_MIN);
  pump.begin(PUMP_RX,PUMP_TX);
  WiFi.setHostname(TELEMETRY_NODE);WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  lastCycle=millis();lastRetry=millis();
  benchLog.print("node_id=" TELEMETRY_NODE " boot_id=%s event=BOOT poll_ms=4000 target_mL_min=%.2f target_source=%s UTC=UNSYNCED transport=MQTT mqtt_lost=0",
    bootID,pump.target,saved?"NVS":"DEFAULT");
}
void loop() {
  if(!correctBoard) {
    // Never silent on the wrong board; the printed MAC is what NODE_MAC must match.
    if(millis()-lastHealth>=5000) {
      lastHealth=millis();
      Serial.printf("node_id=" TELEMETRY_NODE " event=WRONG_BOARD board_mac=%02X:%02X:%02X:%02X:%02X:%02X pump=DISABLED\n",
        boardMac[0],boardMac[1],boardMac[2],boardMac[3],boardMac[4],boardMac[5]);
    }
    delay(100); return;
  }
  char command[128];
  while(telemetry.nextCommand(command,sizeof(command))) pump.submit(command);
  pump.service();
  if(pump.targetDirty) {
    pump.targetDirty=false;
    const bool stored=prefs.putDouble("target",pump.target)==sizeof(double);
    benchLog.print("node_id=" TELEMETRY_NODE " boot_id=%s event=TARGET_SAVED target_mL_min=%.2f nvs=%s",bootID,pump.target,stored?"OK":"FAILED");
  }
  uint32_t now=millis(),ticks=(now-lastCycle)/POLL_MS;
  if(ticks) {
    lastCycle+=ticks*POLL_MS;cycle+=ticks;
    if(ticks>1) benchLog.print("node_id=" TELEMETRY_NODE " event=MISSED_POLL_CYCLES count=%lu",(unsigned long)(ticks-1));
    pump.poll(cycle,lastCycle);
  }
  int status=WiFi.status();
  if(status!=previousWiFi || now-lastWiFiPrint>=5000) {
    previousWiFi=status;
    lastWiFiPrint=now;
    if(status==WL_CONNECTED)
      benchLog.print("[WiFi] Connected | IP=%s | node_id=" TELEMETRY_NODE,WiFi.localIP().toString().c_str());
    else
      benchLog.print("[WiFi] Not connected | status=%d | node_id=" TELEMETRY_NODE,status);
  }
  if(status!=WL_CONNECTED && now-lastRetry>=30000) {lastRetry=now;WiFi.reconnect();}
  if(now-lastHealth>=10000) {
    lastHealth=now;
    benchLog.print("node_id=" TELEMETRY_NODE " boot_id=%s event=HEALTH uptime_ms=%lu pump_ready=%d pump_resets=%lu control_commands=%lu operator_commands=%lu command_lost=%lu UTC=UNSYNCED mqtt_lost=%lu usb_lost=%lu format_lost=%lu line_too_long=%lu queued=%u",
      bootID,(unsigned long)now,pump.ready,(unsigned long)pump.resets,(unsigned long)pump.controls,(unsigned long)pump.operatorCommands,
      (unsigned long)telemetry.commandLost,(unsigned long)telemetry.mqttLost,
      (unsigned long)telemetry.usbLost,(unsigned long)telemetry.formatLost,(unsigned long)benchLog.lost,telemetry.queued());
  }
  benchLog.service();
  delay(1); // Yield to the network/idle task; never wait on network in acquisition.
}
