// Host-only test; .txt prevents Arduino from compiling a second main().
#include "Protocol.h"
#include <assert.h>
#include <math.h>
int main() {
  const uint8_t orpRequest[] = {1,3,0,0,0,2};
  const uint8_t doRequest[] = {1,3,0,0,0,6};
  assert(modbusCRC(orpRequest,6)==0x0BC4);
  assert(modbusCRC(doRequest,6)==0xC8C5);
  uint8_t example[] = {1,3,4,1,0x35,1,1,0x2B,0x91};
  assert(!frameError(example,9,4));
  assert(signedBE16(example+3)==309);
  assert(fabs(signedBE16(example+5)/10.0-25.7)<0.0001);
  const uint8_t negative[] = {0xFF,0x9C};
  const uint8_t minimum[] = {0x80,0};
  assert(signedBE16(negative)==-100);
  assert(signedBE16(minimum)==-32768);
  assert(!strcmp(frameError(example,0,4),"TIMEOUT"));
  assert(!strcmp(frameError(example,4,4),"SHORT_FRAME"));
  assert(!strcmp(frameError(example,9,12),"UNEXPECTED_FRAME"));
  example[3]^=1;
  assert(!strcmp(frameError(example,9,4),"CRC_ERROR"));
  uint8_t exception[] = {1,0x83,2,0,0};
  uint16_t crc=modbusCRC(exception,3);
  exception[3]=crc&255; exception[4]=crc>>8;
  assert(!strcmp(frameError(exception,5,4),"MODBUS_EXCEPTION"));
  uint8_t other[] = {2,3,4,0,0,0,0,0,0};
  crc=modbusCRC(other,7); other[7]=crc&255; other[8]=crc>>8;
  assert(!strcmp(frameError(other,9,4),"WRONG_ADDRESS"));
  const uint8_t one[] = {0x3F,0x80,0,0};
  assert(floatBE(one)==1.0f);
}
