// ESP32-S3 N16R8 bench node02. UART1 EC: RX18 TX17; UART2 pH: RX16 TX15.
// ISCCB-2 host-side VCC must be 3.3V for this direct GPIO wiring.
// NO 12V, NO RS485 adapter. No calibration writes. See README before wiring.
#include <Arduino.h>
#include <WiFi.h>
#include <esp_system.h>
#include "arduino_secrets.h"
#include "BenchLog.h"
BenchLog benchLog;
char bootID[17];
#include "AtlasChannel.h"
HardwareSerial ecUART(1),phUART(2);
AtlasChannel ec(ecUART,"EC_ATLAS_EZO",true),ph(phUART,"PH_ATLAS_EZO",false);
const uint32_t POLL_MS=4000; // bench request cadence, not physical response time
uint32_t lastCycle=0,cycle=0,lastHealth=0,lastRetry=0,lastWiFiPrint=0;
int previousWiFi=-999;
void setup() {
  Serial.begin(115200);
#if ARDUINO_USB_CDC_ON_BOOT && !ARDUINO_USB_MODE
#error Select USB Mode Hardware CDC and JTAG for this tested configuration.
#endif
#if ARDUINO_USB_CDC_ON_BOOT && ARDUINO_USB_MODE
  Serial.setTxTimeoutMs(0);
#endif
  snprintf(bootID,sizeof(bootID),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
  ec.begin(18,17);ph.begin(16,15);
  if(strlen(WIFI_SSID)) {
    WiFi.setHostname("shrimp-node02");WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  }
  lastCycle=millis();lastRetry=millis();
  benchLog.print("node_id=shrimp-node02 boot_id=%s event=BOOT firmware=atlas-bench-0.1 poll_ms=4000 UTC=UNSYNCED transport=USB_ONLY mqtt=NOT_IMPLEMENTED",bootID);
}
void loop() {
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
    if(!strlen(WIFI_SSID))
      benchLog.print("[WiFi] Disabled | SSID not configured | node_id=shrimp-node02");
    else if(status==WL_CONNECTED)
      benchLog.print("[WiFi] Connected | IP=%s | node_id=shrimp-node02",WiFi.localIP().toString().c_str());
    else
      benchLog.print("[WiFi] Not connected | status=%d | node_id=shrimp-node02",status);
  }
  if(strlen(WIFI_SSID) && status!=WL_CONNECTED && now-lastRetry>=30000) {lastRetry=now;WiFi.reconnect();}
  if(now-lastHealth>=10000) {
    lastHealth=now;
    benchLog.print("node_id=shrimp-node02 boot_id=%s event=HEALTH uptime_ms=%lu EC_ready=%d pH_ready=%d usb_log_lost_records=%lu UTC=UNSYNCED",
      bootID,(unsigned long)now,ec.ready,ph.ready,(unsigned long)benchLog.lost);
  }
  benchLog.service();
}
