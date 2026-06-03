/* Function: 100100a8 FUN_100100a8 */


void FUN_100100a8(void)

{
  bool bVar1;
  uint *puVar2;
  
  puVar2 = (uint *)FUN_100111b4(0x1d);
  bVar1 = false;
  if ((((*puVar2 & 4) != 0) && (puVar2[0xe] != 0)) && (puVar2[0xd] == 0)) {
    bVar1 = true;
  }
  FUN_100111d8(0x1d);
  if (bVar1) {
    FUN_10010218(0,0x1a,0,0);
  }
  return;
}


