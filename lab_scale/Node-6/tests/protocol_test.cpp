// Host test: the SEN0710 frames published on https://wiki.dfrobot.com/sen0710/docs/23385 pass Protocol.h.
#include "Protocol.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
int main() {
  const uint8_t request[] = {1,3,0,0,0,2};
  assert(modbusCRC(request,6)==0x0BC4);                 // wire order C4 0B, as in the protocol page
  const uint8_t reply[] = {0x01,0x03,0x04,0x0D,0x2E,0x00,0xDB,0xD8,0xCD};
  assert(!frameError(reply,9,4));
  assert(fabs(((uint16_t(reply[3])<<8)|reply[4])/10.0-337.4)<1e-9);  // turbidity, unsigned
  assert(fabs(signedBE16(reply+5)/10.0-21.9)<1e-9);                  // temperature, signed
  const uint8_t high[] = {0xFF,0xFF};                  // unsigned: 6553.5, never negative
  assert(((uint16_t(high[0])<<8)|high[1])==65535);
  uint8_t bad[9]; memcpy(bad,reply,9); bad[4]^=1;
  assert(!strcmp(frameError(bad,9,4),"CRC_ERROR"));
  assert(!strcmp(frameError(reply,0,4),"TIMEOUT"));
  puts("PASS: SEN0710 request CRC, example reply decode, CRC error, timeout");
}
