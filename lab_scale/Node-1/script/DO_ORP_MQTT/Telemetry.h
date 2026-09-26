#pragma once
#include <Arduino.h>
#include <WiFi.h>
#include <MQTT.h>
#include <esp_timer.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>

// Only the acquisition loop produces records. Only worker() owns the MQTT client.
// Bounded RAM: retain oldest unsent records, drop newest on overflow, count every loss.
class Telemetry : public Print {
  struct Record { char text[1152]; uint64_t captured; uint32_t id; };
  QueueHandle_t pending=nullptr, usb=nullptr;
  char assembling[960]={}, boot[17]={};
  size_t used=0, usbOffset=0;
  bool overflow=false, usbActive=false;
  Record usbRecord={};
  uint32_t nextID=0;
  WiFiClient socket;
  MQTTClient mqtt{256,256};
  char expectedAck[48]={};
  bool acked=false;
  static void task(void* arg) { static_cast<Telemetry*>(arg)->worker(); }
  void worker() {
    mqtt.begin(MQTT_HOST, MQTT_PORT, socket);
    mqtt.setOptions(20, true, 2000);
    mqtt.setWill("shrimp/lab/shrimp-node01/status", "offline", true, 1);
    mqtt.onMessage([this](String &topic, String &payload) {
      if(topic=="shrimp/lab/shrimp-node01/ack" && payload==expectedAck) acked=true;
    });
    uint32_t lastConnect=millis()-5000, lastSend=millis()-5000, inflight=0;
    Record current={};
    char outgoing[1280];
    while(true) {
      uint32_t now=millis();
      if(WiFi.status()!=WL_CONNECTED) { vTaskDelay(pdMS_TO_TICKS(50)); continue; }
      if(!mqtt.connected()) {
        if(now-lastConnect<5000) { vTaskDelay(pdMS_TO_TICKS(20)); continue; }
        lastConnect=now;
        if(!mqtt.connect("shrimp-node01",MQTT_USER,MQTT_PASSWORD)) continue;
        if(!mqtt.subscribe("shrimp/lab/shrimp-node01/ack",1)) { mqtt.disconnect(); continue; }
        mqtt.publish("shrimp/lab/shrimp-node01/status","online",true,1);
        lastSend=millis()-5000;
      }
      mqtt.loop();
      if(inflight && acked) {
        Record removed;
        xQueueReceive(pending,&removed,0);
        inflight=0; acked=false; expectedAck[0]=0;
      }
      if(!inflight && xQueuePeek(pending,&current,0)==pdTRUE) {
        inflight=current.id;
        snprintf(expectedAck,sizeof(expectedAck),"%s:%lu",boot,(unsigned long)inflight);
        acked=false; lastSend=millis()-5000;
      }
      if(inflight && millis()-lastSend>=5000) {
        const uint64_t age=(esp_timer_get_time()-current.captured)/1000;
        int n=snprintf(outgoing,sizeof(outgoing),"%s transport_age_ms=%llu network_buffered=%d",current.text,
                       (unsigned long long)age,age>15000);
        if(n>0 && n<int(sizeof(outgoing)))
          mqtt.publish("shrimp/lab/shrimp-node01/records",outgoing,false,1);
        lastSend=millis();
      }
      vTaskDelay(pdMS_TO_TICKS(10));
    }
  }
public:
  uint32_t mqttLost=0, usbLost=0, formatLost=0;
  bool begin(const char* id) {
    strncpy(boot,id,sizeof(boot)-1);
    pending=xQueueCreate(64,sizeof(Record));
    usb=xQueueCreate(8,sizeof(Record));
    if(!pending || !usb) return false;
    return xTaskCreate(task,"mqttSender",8192,this,1,nullptr)==pdPASS;
  }
  using Print::write;
  size_t write(uint8_t c) override {
    if(c=='\r') return 1;
    if(c!='\n') {
      if(used+1<sizeof(assembling)) assembling[used++]=char(c);
      else overflow=true;
      return 1;
    }
    ++nextID;
    if(overflow || nextID==0) { ++formatLost; used=0; overflow=false; return 1; }
    assembling[used]=0;
    Record record={}; record.captured=esp_timer_get_time(); record.id=nextID;
    snprintf(record.text,sizeof(record.text),"%s transport_boot_id=%s transport_seq=%lu firmware=node01-mqtt-0.1",assembling,boot,(unsigned long)nextID);
    if(!pending || xQueueSend(pending,&record,0)!=pdTRUE) ++mqttLost;
    if(!usb || xQueueSend(usb,&record,0)!=pdTRUE) ++usbLost;
    used=0; return 1;
  }
  unsigned queued() const { return pending?uxQueueMessagesWaiting(pending):0; }
  void serviceUSB() {
    // Hardware CDC is required. No blocking writes when the host is absent/full.
    if(!Serial || !usb) return;
    if(!usbActive) { if(xQueueReceive(usb,&usbRecord,0)!=pdTRUE) return; usbActive=true; usbOffset=0; }
    int room=Serial.availableForWrite(); if(room<=0) return;
    const size_t length=strlen(usbRecord.text);
    if(usbOffset<length) {
      size_t n=length-usbOffset; if(n>size_t(room)) n=room; if(n>64) n=64;
      usbOffset+=Serial.write(reinterpret_cast<const uint8_t*>(usbRecord.text)+usbOffset,n);
    } else { if(Serial.write('\n')==1) usbActive=false; }
  }
};
