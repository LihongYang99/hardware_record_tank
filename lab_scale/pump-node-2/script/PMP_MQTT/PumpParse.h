#pragma once
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <math.h>
// EZO firmware may change reply-prefix case (Node-2 EZO 2.17 answered ?I / ?CAL), so prefixes are case-insensitive.
// Strict decimal parsing: no empty field, NaN, infinity, exponent, hex or trailing junk.
inline bool pumpNumber(const char *s, double &v) {
  const char *p=s; if (*p=='-' || *p=='+') ++p;
  bool digit=false;
  while (*p>='0' && *p<='9') {digit=true; ++p;}
  if (*p=='.') {++p; while (*p>='0' && *p<='9') {digit=true; ++p;}}
  if (!digit || *p) return false;
  char *end; v=strtod(s,&end); return *end==0 && isfinite(v);
}
// "?PV,12.10" / "?TV,5.25"
inline bool pumpField(const char *s, const char *prefix, double &v) {
  size_t n=strlen(prefix);
  return strncasecmp(s,prefix,n)==0 && pumpNumber(s+n,v);
}
// "?i,PMP,1.1": must be a pump, never another EZO circuit.
inline bool pumpIdentity(const char *s) { return strncasecmp(s,"?i,PMP,",7)==0 && s[7]; }
// "?D,<last volume or *>,<1 dispensing | 0 stopped>"
inline bool pumpDispense(const char *s, int &on) {
  if (strncasecmp(s,"?D,",3)) return false;
  const char *last=strrchr(s,',');
  if (last==s+2 || (last[1]!='0' && last[1]!='1') || last[2]) return false;
  char volume[24]; size_t n=last-(s+3);
  if (!n || n>=sizeof(volume)) return false;
  memcpy(volume,s+3,n); volume[n]=0;
  double v;
  if (strcmp(volume,"*") && strcmp(volume,"-*") && !pumpNumber(volume,v)) return false;
  on=last[1]-'0'; return true;
}
// Unsigned decimal within [low, high]; the pump never gets a sign, exponent or "*".
inline bool pumpAmount(const char *s, double low, double high, double &v) {
  return (*s=='.' || (*s>='0' && *s<='9')) && pumpNumber(s,v) && v>=low && v<=high;
}
enum { OP_INVALID=0, OP_START, OP_STOP, OP_DISPENSE, OP_CALIBRATE, OP_QUERY };
// The only operator commands that may reach the pump: constant-rate start, stop, dispense a volume
// (optionally over minutes, for calibration), calibrate/clear calibration, and read-only queries.
// Refused: factory reset, baud/protocol/lock, startup dispense, reverse, full-speed D,*, names, sleep.
inline int pumpOperatorKind(const char *c, double &rate) {
  static const char *const queries[]={"D,?","DC,?","Cal,?","TV,?","ATV,?","PV,?","Status","i"};
  for (const char *q:queries) if (!strcmp(c,q)) return OP_QUERY;
  if (!strcmp(c,"X")) return OP_STOP;
  if (!strcmp(c,"Cal,clear")) return OP_CALIBRATE;
  char buf[40]; double a,b;
  if (strlen(c)>=sizeof(buf)) return OP_INVALID;
  strcpy(buf,c);
  if (!strncmp(buf,"DC,",3)) {
    char *comma=strchr(buf+3,',');
    if (!comma || strcmp(comma,",*")) return OP_INVALID;
    *comma=0;
    if (!pumpAmount(buf+3,0.5,105,a)) return OP_INVALID;
    rate=a; return OP_START;
  }
  if (!strncmp(buf,"D,",2)) {
    char *comma=strchr(buf+2,',');
    if (comma) {*comma=0; if (!pumpAmount(comma+1,0.01,1440,b)) return OP_INVALID;}
    return pumpAmount(buf+2,0.5,1000,a) ? OP_DISPENSE : OP_INVALID;
  }
  if (!strncmp(buf,"Cal,",4)) return pumpAmount(buf+4,0.01,1000,a) ? OP_CALIBRATE : OP_INVALID;
  return OP_INVALID;
}
// "id=<1-20 digits> operator=<1-24 of A-Z a-z 0-9 _ . -> cmd=<command without spaces or '='>"
inline bool pumpOperatorPayload(const char *p, char (&id)[21], char (&op)[25], char (&cmd)[40]) {
  if (strncmp(p,"id=",3)) return false;
  p+=3; size_t n=0;
  while (p[n]>='0' && p[n]<='9') ++n;
  if (!n || n>20 || p[n]!=' ') return false;
  memcpy(id,p,n); id[n]=0; p+=n+1;
  if (strncmp(p,"operator=",9)) return false;
  p+=9; n=0;
  while ((p[n]>='0' && p[n]<='9') || (p[n]>='a' && p[n]<='z') || (p[n]>='A' && p[n]<='Z') || p[n]=='_' || p[n]=='.' || p[n]=='-') ++n;
  if (!n || n>24 || p[n]!=' ') return false;
  memcpy(op,p,n); op[n]=0; p+=n+1;
  if (strncmp(p,"cmd=",4)) return false;
  p+=4; n=strlen(p);
  if (!n || n>=sizeof(cmd)) return false;
  for (size_t i=0;i<n;++i) if (p[i]<=32 || p[i]>126 || p[i]=='=') return false;
  strcpy(cmd,p); return true;
}
// Controller state only: without a flow meter this never proves water is moving.
// 10.8 V is the datasheet minimum motor supply.
inline const char *pumpQC(int on, int intPin, double motorV, double target) {
  if (on!=intPin) return "STATE_MISMATCH";
  if (on && motorV<10.8) return "MOTOR_VOLTAGE_LOW";
  if (target>0 && !on) return "NOT_RUNNING_AS_COMMANDED";
  return "UNVALIDATED";
}
