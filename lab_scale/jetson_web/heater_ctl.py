#!/usr/bin/env python3
"""Gateway thermostat for Node 7 (heater on relay CH1, DECISION 052). Runs inside server.py --pump-control.

Water temperature = mean of the DO probe and turbidity probe temperatures (user choice, 2026-10-12). Every 10 s:
heater ON when automatic control is enabled and the mean is below the setpoint; OFF again at setpoint + HYSTERESIS.
Fail-safe: no setpoint, control disabled, a missing / stale / non-OK / implausible source, or sources disagreeing by
more than MAX_SPREAD all mean OFF. While ON the command is repeated every REFRESH_S; the node opens the relay by
itself 60 s after the last HEAT,ON, so a stopped gateway, broker or network switches the heater off.
"""
import json
import threading
import time

NODE, TOPIC = 'shrimp-node07', 'shrimp/lab/shrimp-node07/cmd'
SOURCES = (('DO_SEN0681', 'temperature_C'), ('TURB_SEN0710', 'temperature_C'))
SETPOINT_RANGE = (5.0, 32.0)    # accepted from the control page
HYSTERESIS = 0.5                # °C above the setpoint before switching off again
MAX_SPREAD = 3.0                # °C allowed between the two probes
FRESH_S = 30                    # a source older than this (incl. transport delay) is not used
PLAUSIBLE = (0.0, 40.0)
PERIOD_S, REFRESH_S, OFF_REPEAT_S = 10, 20, 60


def water_temperature(rows, now):
    """(mean °C or None, reason, {sensor: value}) from Store.latest() rows."""
    values = {}
    for sensor, parameter in SOURCES:
        row = next((r for r in rows if r['sensor_id'] == sensor and r['parameter'] == parameter), None)
        if row is None or row['value'] is None or row['qc_flag'] not in ('OK', 'UNVALIDATED'):
            return None, 'NO_DATA:' + sensor, values
        metadata = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])
        age = str(metadata.get('transport_age_ms', '0'))
        if now - row['received_epoch'] + (int(age) / 1000 if age.isdigit() else float('inf')) > FRESH_S:
            return None, 'STALE:' + sensor, values
        if not PLAUSIBLE[0] <= row['value'] <= PLAUSIBLE[1]:
            return None, 'IMPLAUSIBLE:' + sensor, values
        values[sensor] = row['value']
    if max(values.values()) - min(values.values()) > MAX_SPREAD:
        return None, 'SOURCES_DISAGREE', values
    return sum(values.values()) / len(values), 'OK', values


def decide(enabled, setpoint, temperature, heating, why='NO_TEMPERATURE'):
    """(heater on?, reason). Only ever ON for a valid temperature below the setpoint with control enabled."""
    if not enabled:
        return False, 'DISABLED'
    if setpoint is None:
        return False, 'NO_SETPOINT'
    if temperature is None:
        return False, why
    if temperature < setpoint:
        return True, 'BELOW_SETPOINT'
    if temperature >= setpoint + HYSTERESIS:
        return False, 'AT_SETPOINT'
    return heating, 'HOLD'


class Thermostat:
    def __init__(self, store, conn, publish):
        self.store, self.conn, self.publish = store, conn, publish
        self.wake, self.lock = threading.Event(), threading.Lock()
        self.on, self.sent, self.state = None, 0.0, {}

    def step(self, now=None):
        now = time.time() if now is None else now
        settings = self.store.settings()
        enabled, setpoint = bool(settings.get('heater:enabled', 0)), settings.get('heater:setpoint')
        rows, _ = self.store.latest()
        temperature, why, values = water_temperature(rows, now)
        on, reason = decide(enabled, setpoint, temperature, bool(self.on), why)
        error = None
        if on != self.on or now - self.sent >= (REFRESH_S if on else OFF_REPEAT_S):
            try:
                self.publish(self.conn, f'id={time.time_ns()} operator=thermostat cmd={"HEAT,ON" if on else "HEAT,OFF"}', TOPIC)
                self.sent = now
            except (OSError, ConnectionError):
                error = 'BROKER_UNAVAILABLE'  # the node switches off by itself when ON stops arriving
        if on != self.on:
            note = json.dumps({'temperature_C': temperature, 'setpoint_C': setpoint, 'reason': reason, 'sources': values})
            self.store.log_event(NODE, 'thermostat', 'HEAT,ON' if on else 'HEAT,OFF', note, 'result=' + (error or 'SENT'))
        self.on = on
        relay = next((r for r in rows if r['sensor_id'] == 'HEATER_RELAY' and r['parameter'] == 'relay_on'), None)
        with self.lock:
            self.state = {'enabled': enabled, 'setpoint_C': setpoint, 'temperature_C': temperature, 'sources': values,
                          'heat': on, 'reason': reason, 'error': error, 'relay_on': relay['value'] if relay else None,
                          'hysteresis_C': HYSTERESIS, 'setpoint_range_C': SETPOINT_RANGE, 'checked_epoch': now}

    def snapshot(self):
        with self.lock:
            return dict(self.state)

    def run(self):
        while True:
            try:
                self.step()
            except Exception as error:  # keep looping; the node fails safe on its own
                print(f'thermostat step failed: {error}', flush=True)
            self.wake.wait(PERIOD_S)
            self.wake.clear()
