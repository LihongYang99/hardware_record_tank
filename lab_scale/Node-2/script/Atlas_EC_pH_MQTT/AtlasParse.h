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
