# 100 L Bypass, Pump, and Flow Design

**Revision:** 2026-09-02  
**Purpose:** a small, continuously recirculating, representative sample path for flow monitoring and future validated Mg/Ca or other flow-through sensors. The bypass is not a treatment loop and does not replace tank mixing/aeration.

## 1. Design setpoints

| Parameter | Design value | Acceptance/alarm |
|---|---:|---|
| Tank volume | 100 L nominal | Record actual working volume. |
| Nominal bypass flow | **80 mL/min** | Commissioning operating band 60–100 mL/min. |
| Low-flow alarm | <50 mL/min for 60 s | Stop pump after persistence/retry rule; inspect blockage/leak/air. |
| High-flow alarm | >120 mL/min for 30 s | Stop/correct pump and inspect command/reset state. |
| Wet internal volume | target ≤80 mL; hard gate <100 mL | Measure by fill mass, do not rely only on geometry. |
| Residence time at setpoint | target ≤60 s | `volume / 80 mL/min`; hard gate 75 s at 100 mL. |
| External large-bore tubing | total installed wet length ≤1.2 m | Shorten before increasing chamber volume. |
| Flow acquisition | 1 Hz raw | Publish every raw sample; dashboard may aggregate. |

At 80 mL/min, a volume equal to 100 L passes through the loop in `100,000 / 80 = 1,250 min = 20.8 h`. This is a sampling recirculation rate, not proof that the tank is fully mixed or that one “turnover” makes the sample representative.

## 2. Pump comparison and recommendation

| Pump type | Low-flow control | Sample-contact risk | Failure/maintenance | Result |
|---|---|---|---|---|
| Peristaltic | Strong; positive displacement and calibratable | Fluid contacts only tubing | Pulsation; tube/cassette wear; occlusion can change with age | **Selected recommendation** |
| Diaphragm metering | Possible | Wetted valves/diaphragm require full saline compatibility | Check valves can foul with biofilm/solids; pulsation; more dead volume | Not preferred for this small loop. |
| Small centrifugal | Weak at 80 mL/min without throttling | Impeller/body/seal all wetted | Not self-priming; poor low-flow repeatability; heat and throttling | Rejected for baseline. |
| Gravity/siphon | Level-dependent | Simple tubing | Siphon/runaway risk; changes with tank level and fouling | Rejected for unattended duty. |

**Recommendation — requires promotion of OPEN-09:** Atlas Scientific `EZO-PMP`.

Manufacturer evidence supports 0.5–105 mL/min, self-priming, dry running, calibration, and 12–24 V motor plus 3.3–5.5 V control power. The supplied pump-head tubing is PharMed BPT, 5 mm OD × 3 mm ID. Stated life is >1,000 h for tubing, 1,500 h for cassette, and 5,000 h for motor. These are only about 42, 63, and 208 days at 24/7 operation, so this pump is serviceable rather than maintenance-free.

Important controller limitation: `Dstart,*` starts continuous pumping at approximately 105 mL/min. It cannot encode an indefinite 80 mL/min setpoint. Constant-rate operation uses `DC,80,*`, and the pump documents an internal reset after 20 days of continuous mode. Therefore Node 4 must supervise and reissue the setpoint through the isolated I2C bus. A tested `Dstart,*` may act as a safe temporary restart at ~105 mL/min, within the 120 mL/min high alarm, until Node 4 restores 80 mL/min.

Source: [EZO-PMP datasheet](https://files.atlas-scientific.com/EZO_PMP_Datasheet.pdf).

## 3. Flow-meter recommendation

**Recommendation — requires promotion of OPEN-10:** Sensirion `EK-SLF3S-4000B` evaluation kit for the first build.

Reasons:

- ±600 mL/min water range contains 60–100 mL/min with margin;
- low internal volume (~58 µL) and 5–6 mm recommended tubing ID;
- I2C with per-word CRC and documented address `0x08`;
- kit includes the otherwise separate clamp and pigtail;
- wetted PPS/316L/epoxy materials are documented.

The manufacturer calibration fluids are water and isopropanol, not 15–25 ppt saline water. Accept it as a flow-presence/relative monitor, then establish a versioned gravimetric correction at 60, 80, and 100 mL/min. Do not copy the water accuracy claim to the shrimp-water record. Its air-in-line indication is not an approved safety function in this matrix.

The sensor must use the DFR0565 isolated I2C path and a 3.3 V regulator as specified in `WIRING_AND_GPIO.md`.

Sources: [SLF3S-4000B product](https://sensirion.com/products/catalog/SLF3S-4000B), [SLF3S-4000B datasheet](https://sensirion.com/resource/datasheet/slf3s-4000b).

## 4. Exact hydraulic order

```text
Tank, representative mid-depth intake
  → removable coarse intake guard (≥1 mm, low dead volume)
  → short 5–6 mm-ID suction tube
  → reducer to Atlas pump connector
  → EZO-PMP / 3 mm-ID PharMed BPT pump-head tube
  → reducer back to 5–6 mm-ID pressure tube
  → accessible 100-mesh service filter (conditional after fouling test)
  → short vertical clear inspection/pulse-compliance section (only if required)
  → Sensirion SLF3S-4000B, arrow in return-flow direction
  → removable blank spool / future ≤40 mL flow chamber
  → normally capped sample tee, sample goes to waste
  → return tube
  → secured outlet 5–10 mm above normal water surface, directed against tank wall
```

### Why this order

- A coarse intake guard protects shrimp and excludes large debris without imposing a fine-filter suction head.
- The peristaltic pump is upstream of analytical hardware, providing positive flow and self-priming.
- A service filter after the pump protects the flow sensor and future chamber; its clogging is detected as low flow. The filter is conditional because fouling rate must be observed.
- Flow is measured immediately before the chamber so chamber exposure is traceable.
- The sample tee after the chamber produces time-aligned reference samples without returning cleaning/reagent waste.
- A minimal 5–10 mm air gap breaks a siphon and gives visible return confirmation while minimizing waterfall aeration. Verify by pump-on/off spatial DO commissioning; if it measurably changes the experiment, propose a submerged-return/anti-siphon redesign under change control.

There is no baseline needle valve. Pump speed is the flow control; throttling a peristaltic pump adds pressure and dead volume without improving the setpoint. There is no baseline check valve because the pump occlusion and return air gap prevent a free siphon; add one only after a documented failure analysis and saline-material review.

## 5. Tubing and fitting specification

### Pump head

- Atlas cassette tube: Saint-Gobain PharMed BPT, 5 mm OD × 3 mm ID, 15.24 cm.
- Atlas inline connectors: HDPE, approximately 4.8 mm hose nipple OD and 2.8 mm bore.
- Replacement cassette: `PMP-RC`; keep one onsite before continuous use.

### External loop

- Nominal ID: **5–6 mm**, with 6 mm preferred where it fits the Sensirion barb/clamp.
- Material: PharMed BPT or an equivalent whose manufacturer explicitly supports concentrated NaCl/brackish water and the actual temperature/cleaning chemistry.
- No copper, brass, plain steel, PVC plasticizer of unknown composition, or natural rubber in the wetted path.
- Barbs/fittings: PP, PVDF, HDPE, PEEK, or documented 316L; seals EPDM/FKM only after compatibility with salinity and cleaning chemistry is confirmed.
- Every pressurized barb is mechanically clamped. The Sensirion sensor uses its manufacturer clamp.

Saint-Gobain’s compatibility guide rates PharMed BPT/TPE excellent for 20% sodium chloride, which is more concentrated than 15–25 ppt. The exact metric tube OD and supplier SKU remain a dimensional procurement gate because the pump connector and flow-meter barb must be physically test-fitted.

Sources: [Atlas premium tubing specification](https://files.atlas-scientific.com/premium_tubing_specs2.pdf), [Saint-Gobain compatibility guide](https://www.biopharm.saint-gobain.com/sites/hps-mac3-lifesciences-bioprocess/files/chemical-compatibility-chart-bps_0.pdf).

## 6. Internal-volume budget

Use this as an allocation; final volume is determined by filling the assembled, drained loop with water and weighing the mass.

| Component | Geometry/allocation | Budget |
|---|---|---:|
| 1.2 m of 6 mm-ID tubing | `π × 3² × 1200 mm` | 33.9 mL |
| Pump-head tubing | 3 mm ID × 152.4 mm | 1.1 mL |
| SLF3S-4000B | manufacturer value | 0.058 mL |
| Filter and fittings | allocation; verify by fill | ≤5 mL |
| Optional inspection/pulse section | only if required | ≤10 mL |
| Provisional/future chamber | hard design limit | ≤40 mL |
| **Worst allocated total** | all optional capacity used | **≤90.1 mL** |

At 80 mL/min, 90.1 mL corresponds to 67.6 s. The target remains ≤80 mL/60 s: reduce tubing and omit the optional inspection section where possible. The hard limits are <100 mL and <75 s at setpoint.

The final chamber cannot be ordered yet. Ca/Mg probe immersion depth, diameter, orientation, thread, flow sensitivity, and reference-junction requirements are unknown. Until validated models exist, install a removable blank spool of measured volume and capped future ports; do not drill guessed ports.

## 7. Pump and flow control state machine

| State | Entry | Action | Exit/fault |
|---|---|---|---|
| `SAFE_OFF` | boot, maintenance, leak, manual stop | Pump command off; record flow zero check. | Operator/run permit. |
| `PRIME` | run permit | Start at controlled rate; maximum 30 s. | Flow >50 mL/min → `RUN`; timeout → `FAULT_LOW_FLOW`. |
| `RUN` | valid pump/flow identities | Send/verify `DC,80,*`; acquire raw flow at 1 Hz. | Low/high persistence, I2C loss, leak, maintenance. |
| `RECOVER_RESET` | pump identity/status/flow indicates 20-day reset or power recovery | Revalidate path; reissue `DC,80,*`; annotate reset. | Stable 60–100 → `RUN`; otherwise fault. |
| `FAULT_LOW_FLOW` | <50 mL/min for 60 s | Stop pump; latch alarm; never hammer a blocked line. | Inspection/acknowledged retry. |
| `FAULT_HIGH_FLOW` | >120 mL/min for 30 s | Stop/correct; check `Dstart,*` or calibration. | Inspection/acknowledged restart. |
| `MAINTENANCE` | manual command | Stop, divert outlet/sample to waste, suppress process alarms but flag all data. | Rinse, restore valves/caps, leak check, operator release. |

Do not implement autonomous chemical dosing or water-quality control in Phase 1. Node 4 controls only bypass circulation and safety.

## 8. Gravimetric calibration

1. Assemble the exact final tubing, filter, chamber/spool, height, and return.
2. Fill with tank-salinity water at recorded temperature; purge bubbles.
3. Zero the flow meter with confirmed zero flow.
4. At commanded 60, 80, and 100 mL/min, collect the outlet for 10 minutes into a tared vessel.
5. Convert mass to volume using independently measured/traceable brackish-water density at that temperature.
6. Run at least three replicates per setpoint, randomizing order if practical.
7. Record raw I2C values/CRC, mean, standard deviation, mass, time, density, temperature, command, cassette age, and calibration version.
8. Fit the simplest justified correction. If residual error exceeds the experimental requirement, report that limitation rather than applying an opaque model.
9. Recheck weekly initially and after any tube/cassette/filter/geometry change.

Pump calibration and flow-sensor calibration are separate: a calibrated pump does not validate the flow sensor, and a calibrated flow sensor does not remove pump wear.

## 9. Representativeness commissioning

Run the locked spatial study before treating the bypass sample as tank representative:

- map DO, temperature, pH/EC, and salinity at top/mid/bottom and near/far from aeration, intake, and return;
- compare bypass sample-port measurements with a simultaneous grab at the intake location;
- repeat with bypass pump off and on to detect return-induced mixing/aeration;
- document shrimp stocking/activity and feeding state;
- choose an intake that does not settle into sludge, entrain surface foam, or sit in the return jet.

The intake is anchored at the selected mid-depth location and the return is on the opposite/downstream side. Both are strain-relieved so shrimp activity cannot move them.

## 10. Maintenance plan

| Interval, initial | Task | Data annotation |
|---|---|---|
| Daily | Visual return, leaks, bubbles, kink, filter loading, flow trend | Event only if action/abnormality. |
| Weekly | Gravimetric spot check; inspect intake/filter; compare pump command vs flow | Calibration/check event. |
| 30 days | Planned pump tube/cassette inspection and likely preventive replacement during early operation | `MAINTENANCE`; new cassette/tube asset ID. |
| ≤1,000 h | Replace pump tubing no later than manufacturer life unless a stricter validated interval is adopted | Mandatory. |
| ≤1,500 h | Replace cassette no later than stated life | Mandatory. |
| After any wet-path change | Leak test, volume measurement, purge, three-point flow recalibration | New configuration/calibration version. |
| Before/after chemical cleaning | Divert to waste; compatible rinse until blank/reference is acceptable | Never return cleaner to tank. |

The exact maintenance interval may become shorter with biofilm and solids. It cannot become longer than manufacturer life without documented reliability evidence.

## 11. Bypass acceptance tests

- [ ] 24 h leak-free operation with electronics dry and drip tray empty.
- [ ] Self-prime from the installed lift without >30 s dry run.
- [ ] Three-point gravimetric calibration passes the stated experiment accuracy requirement.
- [ ] Total wet volume measured <100 mL; target ≤80 mL.
- [ ] Low-flow fault from pinched intake stops pump and records alarm/raw flow.
- [ ] High-flow/reset case is detected; Node 4 restores 80 mL/min.
- [ ] Power interruption at pump, Node 4, router, and Pi recovers without unsafe pumping or lost audit trail.
- [ ] Filter loading is observable and does not silently bias flow.
- [ ] Pump-on/off spatial study finds no unacceptable DO/salinity perturbation.
- [ ] Sample/cleaning waste cannot be returned accidentally to the tank.
- [ ] Final chamber remains blocked until exact validated probe models define ports and geometry.
