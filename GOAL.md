# GOAL.md
# Aquaculture Real-Time Monitoring Platform

## 1. Project Goal

Design and build a complete, research-grade, real-time water-quality monitoring platform for a round polyethylene Litopenaeus vannamei shrimp tank with a nominal capacity of 340 L (90 US gallons). Actual operating water volume is to be confirmed.

The system must be practical enough that I can:

1. purchase all required hardware,
2. assemble all electrical connections,
3. install the sensors,
4. build the bypass loop,
5. deploy multiple ESP32 sensor nodes,
6. continuously acquire timestamped measurements,
7. send the data over Wi-Fi,
8. collect the data on a Raspberry Pi,
9. store raw data in a database,
10. visualize the data in real time,
11. later use an NVIDIA Jetson Orin for edge computing and machine learning.

find link, name and purpose of all required hardaware components for me to use.
This is an engineering implementation project, not only a sensor-selection project.

The final system should be modular, scientifically defensible, electrically safe, reliable for long-term experiments, and easy to troubleshoot.

---

# 2. Highest-Priority Objective

The first and most important objective is:

> Build a reliable real-time monitoring platform with accurate timestamps.

The initial end-to-end data path must be:

Sensor  
→ interface / signal converter  
→ ESP32  
→ UTC timestamp  
→ Wi-Fi  
→ MQTT  
→ Raspberry Pi  
→ database  
→ real-time dashboard

Machine learning is NOT the first priority.

The Jetson Orin must not be required for basic monitoring.

The monitoring platform must continue working when the Jetson is offline.

---

# 3. Experimental Context

System:

- round polyethylene aquaculture tank, nominal capacity 340 L (90 US gallons; rounded nominal capacities)
- internal diameter: 39 in (99.06 cm)
- tank depth: 20 in (50.8 cm); this is not the operating water depth
- actual operating water depth and volume: NOT VERIFIED; to be confirmed
- Pacific white shrimp
- Litopenaeus vannamei
- brackish / saline water
- approximately 15–25 ppt salinity
- experiments lasting weeks to months
- continuous 24/7 operation

The platform must be designed for long-term deployment next to saline water.

Reliability, corrosion resistance, waterproofing, cable management, biofouling, maintenance, and calibration must therefore be considered from the beginning.

---

# 4. Monitoring Parameters

The target system should cover the following parameters where scientifically and technically feasible.

## Mid-Water Representative Station

- dissolved oxygen
- temperature
- pH
- EC
- salinity
- turbidity / eTSS
- NH4+ if scientifically feasible

## Bottom-Risk Station

- dissolved oxygen
- ORP
- dissolved H2S

## Bypass / Flow-Through System

- Mg2+
- Ca2+
- flow rate
- other sensors that are better suited to a flow-through configuration

## Online / External Chemistry

Where direct submerged continuous sensing is not scientifically reliable, evaluate external or automated measurements for:

- NO2-N
- NO3-N
- alkalinity
- TAN reference measurements

Do not force every parameter into a direct submerged sensor if that measurement would not be scientifically valid.

---

# 5. Preferred Computing Architecture

I already have:

- Raspberry Pi
- NVIDIA Jetson Orin

Preferred overall architecture:

```text
Water-quality sensors
        ↓
ESP32 sensor nodes
        ↓
Wi-Fi / MQTT
        ↓
Raspberry Pi
        ↓
Database + dashboard + data storage
        ↓
Jetson Orin
        ↓
Future edge AI / ML
