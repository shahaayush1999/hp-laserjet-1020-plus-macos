/* Function: 100171e0 FUN_100171e0 */


void FUN_100171e0(uint param_1)

{
  undefined1 in_INTCLEAR;
  
  wsr(in_INTCLEAR,1 << 0x20 - (0x20 - (param_1 & 0x1f)));
  return;
}


