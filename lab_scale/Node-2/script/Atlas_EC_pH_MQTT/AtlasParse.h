#pragma once
#include <stdlib.h>
#include <string.h>
#include <math.h>
// Device firmware 2.17 returns ?I; older documented examples use ?i.
// Keep the model match strict so EC and pH cannot be silently swapped.
inline bool atlasIdentity(const char *s, bool ec) {
  if (strlen(s)<7 || s[0]!='?' || (s[1]!='i' && s[1]!='I')) return false;
  return strncmp(s+2,ec?",EC,":",pH,",4)==0;
}
// Strict decimal parsing: no empty fields, NaN, infinity, hex or trailing junk.
inline bool atlasNumber(const char *s, double &v) {
  const char *p=s; if (*p=='-' || *p=='+') ++p;
  bool digit=false;
  while (*p>='0' && *p<='9') {digit=true; ++p;}
  if (*p=='.') {++p; while (*p>='0' && *p<='9') {digit=true; ++p;}}
  if (!digit || *p) return false;
  char *end; v=strtod(s,&end); return *end==0 && isfinite(v);
}
inline bool atlasValues(const char *s, bool ec, double &a, double &b) {
  if (!ec) return atlasNumber(s,a);
  const char *comma=strchr(s,',');
  if (!comma || strchr(comma+1,',') || comma-s>48) return false;
  char first[50]; memcpy(first,s,comma-s); first[comma-s]=0;
  return atlasNumber(first,a) && atlasNumber(comma+1,b);
}
// Unsigned decimal within [low, high]: no sign, exponent or text.
inline bool atlasAmount(const char *s, double low, double high) {
  double v; return (*s=='.' || (*s>='0' && *s<='9')) && atlasNumber(s,v) && v>=low && v<=high;
}
// Operator calibration commands (MQTT sketch only; ezo_cal.py builds the same set). Startup never sends these.
// EC: K,10 (the K 10 probe), Cal,dry, Cal,low|high,<uS/cm>, single-point Cal,<uS/cm>. pH: Cal,mid|low|high,<pH>.
// Both: Cal,clear and read-only queries. Refused: Factory, T,<n>, O,..., Baud, I2C, Name, Plock, Sleep, Find, any other K.
inline bool atlasOperatorCommand(const char *c, bool ec) {
  static const char *const exact[]={"Cal,?","Cal,clear","T,?","K,?","K,10","Cal,dry","Slope,?"};
  for (int i=0;i<7;++i) if (!strcmp(c,exact[i])) return i<3 || (ec ? i<6 : i==6);
  if (strncmp(c,"Cal,",4)) return false;
  c+=4;
  if (ec) {
    if (!strncmp(c,"low,",4) || !strncmp(c,"high,",5)) c=strchr(c,',')+1;
    return atlasAmount(c,10,500000); // K 10 probe range starts at 10 uS/cm
  }
  if (!strncmp(c,"mid,",4)) return atlasAmount(c+4,6.5,7.5);
  if (!strncmp(c,"low,",4)) return atlasAmount(c+4,1,6);
  return !strncmp(c,"high,",5) && atlasAmount(c+5,8,13);
}
// "id=<1-20 digits> operator=<1-24 of A-Z a-z 0-9 _ . -> cmd=<EC|PH>:<command, 1-31 chars without spaces or '='>"
inline bool atlasOperatorPayload(const char *p, char (&id)[21], char (&op)[25], bool &ec, char (&cmd)[32]) {
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
  if (!strncmp(p,"cmd=EC:",7)) ec=true;
  else if (!strncmp(p,"cmd=PH:",7)) ec=false;
  else return false;
  p+=7; n=strlen(p);
  if (!n || n>=sizeof(cmd)) return false;
  for (size_t i=0;i<n;++i) if (p[i]<=32 || p[i]>126 || p[i]=='=') return false;
  strcpy(cmd,p); return true;
}
