// Lab MQTT variant of Atlas_EC_pH_UART. AtlasChannel.h / AtlasParse.h are byte-identical copies.
// ESP32-S3 N16R8 bench node02. UART1 EC: RX18 TX17; UART2 pH: RX16 TX15.
// ISCCB-2 host-side VCC must be 3.3V for this direct GPIO wiring.
// NO 12V, NO RS485 adapter. No calibration/K/temperature writes. UTC remains UNSYNCED.
#include <Arduino.h>
#include <WiFi.h>
#include <esp_system.h>
#include <esp_mac.h>
#include "arduino_secrets.h"
#define TELEMETRY_NODE "shrimp-node02"
#define TELEMETRY_FIRMWARE "node02-mqtt-0.1"
#include "Telemetry.h"
Telemetry telemetry;
#include "BenchLog.h"
BenchLog benchLog;
char bootID[17];
#include "AtlasChannel.h"
HardwareSerial ecUART(1),phUART(2);
AtlasChannel ec(ecUART,"EC_ATLAS_EZO",true),ph(phUART,"PH_ATLAS_EZO",false);
const uint32_t POLL_MS=4000; // bench request cadence, not physical response time
uint32_t lastCycle=0,cycle=0,lastHealth=0,lastRetry=0,lastWiFiPrint=0;
int previousWiFi=-999;
bool correctBoard=false;
void setup() {
  Serial.begin(115200);
#if !ARDUINO_USB_CDC_ON_BOOT || !ARDUINO_USB_MODE
#error Select USB CDC On Boot enabled and USB Mode Hardware CDC and JTAG.
#endif
  Serial.setTxTimeoutMs(0);
  // Factory base MAC from eFuse; never run Node 2 sensor commands on another board.
  const uint8_t node2Mac[6]={0x44,0xB1,0x76,0xCC,0xD4,0x84};
  uint8_t mac[6]={};
  correctBoard=esp_efuse_mac_get_default(mac)==ESP_OK && memcmp(mac,node2Mac,6)==0;
  if(!correctBoard) return;
  snprintf(bootID,sizeof(bootID),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
  if(!telemetry.begin(bootID)) { correctBoard=false; return; }
  ec.begin(18,17);ph.begin(16,15);
  WiFi.setHostname("shrimp-node02");WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  lastCycle=millis();lastRetry=millis();
  benchLog.print("node_id=shrimp-node02 boot_id=%s event=BOOT poll_ms=4000 UTC=UNSYNCED transport=MQTT mqtt_lost=0",bootID);
}
void loop() {
  if(!correctBoard) {
    // Direct, non-blocking notice so a wrong board is never silent.
    if(millis()-lastHealth>=5000) { lastHealth=millis(); Serial.println("node_id=shrimp-node02 event=WRONG_BOARD sensors=DISABLED"); }
    delay(100); return;
  }
  ec.service();ph.service();
  uint32_t now=millis(),ticks=(now-lastCycle)/POLL_MS;
  if(ticks) {
    lastCycle+=ticks*POLL_MS;cycle+=ticks;
    if(ticks>1) benchLog.print("node_id=shrimp-node02 event=MISSED_POLL_CYCLES count=%lu",(unsigned long)(ticks-1));
    ec.poll(cycle,lastCycle);ph.poll(cycle,lastCycle);
  }
  int status=WiFi.status();
  if(status!=previousWiFi || now-lastWiFiPrint>=5000) {
    previousWiFi=status;
    lastWiFiPrint=now;
    if(status==WL_CONNECTED)
      benchLog.print("[WiFi] Connected | IP=%s | node_id=shrimp-node02",WiFi.localIP().toString().c_str());
    else
      benchLog.print("[WiFi] Not connected | status=%d | node_id=shrimp-node02",status);
  }
  if(status!=WL_CONNECTED && now-lastRetry>=30000) {lastRetry=now;WiFi.reconnect();}
  if(now-lastHealth>=10000) {
    lastHealth=now;
    benchLog.print("node_id=shrimp-node02 boot_id=%s event=HEALTH uptime_ms=%lu EC_ready=%d pH_ready=%d UTC=UNSYNCED mqtt_lost=%lu usb_lost=%lu format_lost=%lu line_too_long=%lu queued=%u",
      bootID,(unsigned long)now,ec.ready,ph.ready,(unsigned long)telemetry.mqttLost,(unsigned long)telemetry.usbLost,
      (unsigned long)telemetry.formatLost,(unsigned long)benchLog.lost,telemetry.queued());
  }
  benchLog.service();
  delay(1); // Yield to the network/idle task; never wait on network in acquisition.
}
