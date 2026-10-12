// Host test for the heater command parser and the dead-man timeout (no ESP32 needed).
#include <assert.h>
#include <stdio.h>
#include "../script/HEATER_MQTT/HeaterLogic.h"
int main() {
  assert(heaterCommand("id=1 operator=thermostat cmd=HEAT,ON")==1);
  assert(heaterCommand("id=2 operator=web-li cmd=HEAT,OFF")==0);
  const char *bad[]={"cmd=HEAT,ON","id=3 operator=x cmd=HEAT,ON ","id=4 operator=x cmd=heat,on","id=5 operator=x cmd=HEAT,ONX",
                     "id=6 operator=x cmd=X","id=7 operator=x","","HEAT,ON"};
  for (const char *b : bad) assert(heaterCommand(b)==-1);
  assert(!heaterExpired(59999,0,60000) && heaterExpired(60000,0,60000));
  assert(!heaterExpired(10,4294967000u,60000));          // millis() wrap: 306 ms elapsed
  assert(heaterExpired(70000,4294967000u,60000));
  puts("PASS: HEAT,ON/OFF only, strict envelope, dead-man timeout incl. millis wrap");
}
