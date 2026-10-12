#pragma once
#include <stdint.h>
#include <string.h>
// Pure logic, host-tested. Payload envelope is the pumps': "id=<digits> operator=<name> cmd=<command>".
// Returns 1 for HEAT,ON, 0 for HEAT,OFF, -1 for anything else (ignored and logged by the caller).
inline int heaterCommand(const char *payload) {
  const char *c = strstr(payload, " cmd=");
  if (strncmp(payload, "id=", 3) || !c) return -1;
  if (!strcmp(c + 5, "HEAT,ON")) return 1;
  if (!strcmp(c + 5, "HEAT,OFF")) return 0;
  return -1;
}
// The relay may stay on only while the gateway keeps repeating HEAT,ON (dead-man). Unsigned math survives millis() wrap.
inline bool heaterExpired(uint32_t now, uint32_t lastOn, uint32_t holdMs) { return now - lastOn >= holdMs; }
