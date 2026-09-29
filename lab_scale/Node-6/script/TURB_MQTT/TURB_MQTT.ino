// Node 6 (shrimp-node06): DFRobot SEN0710 turbidity, Modbus RTU over RS485, the only sensor on this node.
// UART1 RX18 <- converter TXD, TX17 -> converter RXD; 4800 8N1, address 1 (factory defaults).
// Protocol: https://wiki.dfrobot.com/sen0710/docs/23385 — function 03, registers 0-1:
// turbidity uint16 / 10 NTU, temperature int16 / 10 °C. Read only: never writes address, baud or calibration.
// Protocol.h and BenchChannel.h are byte-identical to Node-1; Telemetry.h to Node-2. UTC remains UNSYNCED.
#include <Arduino.h>
#include <WiFi.h>
#include <esp_system.h>
#include <esp_mac.h>
#include "arduino_secrets.h"
#define TELEMETRY_NODE "shrimp-node06"
#define TELEMETRY_FIRMWARE "node06-mqtt-0.1"
#include "Protocol.h"
#include "BenchChannel.h"
#include "Telemetry.h"
Telemetry telemetry;
// Factory MAC of the Node 6 ESP32, read with esptool before flashing. All zeros never polls the sensor.
const uint8_t NODE_MAC[6]={0x44,0xB1,0x76,0xCE,0xD8,0x6C}; // esptool flash-id, 2026-09-29
const uint32_t POLL_INTERVAL_MS=4000; // same cadence as Node 1; datasheet response time is <=30 s
HardwareSerial turbUART(1);
BenchChannel turb(turbUART,"TURB_SEN0710",2,POLL_INTERVAL_MS);
bool correctBoard=false;
uint32_t lastCycle=0,cycleNumber=0,lastHealth=0,lastWiFiPrint=0,lastWiFiRetry=0;
char bootID[17];

void report(BenchChannel& c) {
  telemetry.printf("node_id=" TELEMETRY_NODE " boot_id=%s sensor=%s seq=%lu request_uptime_ms=%lu rx_uptime_ms=",
                   bootID,c.id,(unsigned long)c.seq,(unsigned long)c.started);
  if (c.length) telemetry.printf("%lu",(unsigned long)c.lastByte); else telemetry.print("NA");
  telemetry.printf(" cycle=%lu scheduled_uptime_ms=%lu report_uptime_ms=%lu UTC=UNSYNCED raw=",
                   (unsigned long)c.cycle,(unsigned long)c.scheduled,(unsigned long)millis());
  for (size_t i=0;i<c.length;++i) telemetry.printf("%02X",c.raw[i]);
  if (c.dropped) { telemetry.printf(" COMM=ERROR QC=COMMUNICATION_ERROR reason=RX_OVERFLOW dropped_bytes=%lu\n",(unsigned long)c.dropped); return; }
  const char* error=frameError(c.raw,c.length,c.registers*2);
  if (error) {
    telemetry.printf(" COMM=ERROR QC=COMMUNICATION_ERROR reason=%s",error);
    if (!strcmp(error,"MODBUS_EXCEPTION")) telemetry.printf(" exception_code=%u",c.raw[2]);
    telemetry.println();
    return;
  }
  const float ntu=((uint16_t(c.raw[3])<<8)|c.raw[4])/10.0f; // unsigned per the protocol page
  const float temperature=signedBE16(c.raw+5)/10.0f;
  // 0-1000 NTU is the datasheet range; the temperature channel's range is NOT VERIFIED, so it is not range-checked.
  telemetry.printf(" turbidity_NTU=%.1f temperature_C=%.1f COMM=OK QC=%s\n",ntu,temperature,ntu<=1000?"UNVALIDATED":"OUT_OF_RANGE");
}

void service(BenchChannel& c,bool pollDue) {
  uint32_t now=millis();
  if (pollDue && c.waiting) telemetry.printf("sensor=%s cycle=%lu QC=STALE reason=POLL_SKIPPED_BUSY\n",c.id,(unsigned long)cycleNumber);
  if (!c.waiting) {
    int pending=c.uart.available(); // late/unrequested bytes are logged, never parsed as a reading
    if (pending>0) {
      if (pending>128) pending=128;
      telemetry.printf("node_id=" TELEMETRY_NODE " boot_id=%s sensor=%s uptime_ms=%lu UNSOLICITED_RAW=",bootID,c.id,(unsigned long)now);
      while (pending-->0) telemetry.printf("%02X",c.uart.read());
      telemetry.println();
      if (pollDue) telemetry.printf("sensor=%s cycle=%lu QC=COMMUNICATION_ERROR reason=POLL_SKIPPED_UNSOLICITED\n",c.id,(unsigned long)cycleNumber);
      return;
    }
    if (!pollDue) return;
    uint8_t request[]={1,3,0,0,0,c.registers,0,0};
    const uint16_t crc=modbusCRC(request,6);
    request[6]=crc&0xFF; request[7]=crc>>8;
    c.length=c.dropped=0; c.started=c.lastPoll=now; c.cycle=cycleNumber; c.scheduled=lastCycle; ++c.seq; c.waiting=true;
    c.uart.write(request,sizeof(request));
  }
  int pending=c.uart.available();
  if (pending>128) pending=128;
  while (pending-->0) {
    const uint8_t b=c.uart.read();
    if (c.length<sizeof(c.raw)) c.raw[c.length++]=b;
    else { telemetry.printf("sensor=%s seq=%lu OVERFLOW_RAW=%02X\n",c.id,(unsigned long)c.seq,b); ++c.dropped; }
    c.lastByte=millis();
  }
  now=millis();
  if ((c.length && now-c.lastByte>=30) || now-c.started>=1000) { report(c); c.waiting=false; }
}

void setup() {
  Serial.begin(115200);
#if !ARDUINO_USB_CDC_ON_BOOT || !ARDUINO_USB_MODE
#error Select USB CDC On Boot enabled and USB Mode Hardware CDC and JTAG.
#endif
  Serial.setTxTimeoutMs(0);
  WiFi.mode(WIFI_STA);
  const uint8_t unset[6]={};
  uint8_t mac[6]={};
  correctBoard=esp_efuse_mac_get_default(mac)==ESP_OK && memcmp(NODE_MAC,unset,6) && !memcmp(mac,NODE_MAC,6);
  if (!correctBoard) return; // never poll this node's sensor on another board
  snprintf(bootID,sizeof(bootID),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
  if (!telemetry.begin(bootID)) { correctBoard=false; return; }
  turbUART.begin(4800,SERIAL_8N1,18,17);
  WiFi.setHostname(TELEMETRY_NODE);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  lastWiFiRetry=lastCycle=millis();
  telemetry.printf("node_id=" TELEMETRY_NODE " boot_id=%s event=BOOT UTC=UNSYNCED transport=MQTT mqtt_lost=0\n",bootID);
}

void loop() {
  if (!correctBoard) {
    if (millis()-lastHealth>=5000) { lastHealth=millis(); Serial.println("node_id=" TELEMETRY_NODE " event=WRONG_BOARD sensors=DISABLED"); }
    delay(100); return;
  }
  const uint32_t now=millis(), ticks=(now-lastCycle)/POLL_INTERVAL_MS;
  if (ticks) {
    lastCycle+=ticks*POLL_INTERVAL_MS; cycleNumber+=ticks;
    if (ticks>1) telemetry.printf("QC=STALE reason=MISSED_POLL_CYCLES count=%lu\n",(unsigned long)(ticks-1));
  }
  service(turb,ticks>0);
  if (!turb.waiting) { // network maintenance between transactions
    if (now-lastWiFiPrint>=5000) {
      lastWiFiPrint=now;
      if (WiFi.status()==WL_CONNECTED) { telemetry.print("[WiFi] Connected | IP="); telemetry.println(WiFi.localIP()); }
      else telemetry.println("[WiFi] Not connected");
    }
    if (WiFi.status()!=WL_CONNECTED && now-lastWiFiRetry>=30000) { lastWiFiRetry=now; WiFi.reconnect(); }
  }
  if (now-lastHealth>=10000) {
    lastHealth=now;
    telemetry.printf("node_id=" TELEMETRY_NODE " boot_id=%s event=HEALTH uptime_ms=%lu UTC=UNSYNCED mqtt_lost=%lu usb_lost=%lu format_lost=%lu queued=%u\n",
      bootID,(unsigned long)now,(unsigned long)telemetry.mqttLost,(unsigned long)telemetry.usbLost,(unsigned long)telemetry.formatLost,telemetry.queued());
  }
  telemetry.serviceUSB();
  delay(1);
}
