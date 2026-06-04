/* Function: 10011c44 FUN_10011c44 */


undefined4 FUN_10011c44(uint param_1,uint param_2)

{
  uint *puVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  undefined4 local_30;
  
  local_30 = 0;
  if (*PTR_DAT_100064bc == '\x01') {
    param_1 = param_1 | param_2 >> 7 & 0xe;
  }
  FUN_10011b20();
  puVar1 = DAT_100064cc;
  uVar3 = 0x80;
  uVar4 = 0;
  do {
    FUN_100116ec(1);
    if ((uVar3 & param_1 & 0xff) == 0) {
      memw();
      uVar5 = *puVar1 & DAT_100064c8;
    }
    else {
      memw();
      uVar5 = *puVar1 | DAT_10005e80;
    }
    memw();
    *puVar1 = uVar5;
    FUN_100116ec(1);
    uVar5 = DAT_100064d0;
    memw();
    uVar3 = uVar3 >> 1;
    memw();
    *puVar1 = *puVar1 | DAT_100064d0;
    FUN_100116ec(2);
    uVar2 = DAT_100064d4;
    memw();
    uVar4 = uVar4 + 1;
    memw();
    *puVar1 = *puVar1 & DAT_100064d4;
  } while (uVar4 < 8);
  FUN_100116ec(2);
  puVar1 = DAT_100064cc;
  memw();
  memw();
  *DAT_100064c4 = *DAT_100064c4 & DAT_100064c8;
  memw();
  memw();
  *puVar1 = *puVar1 | uVar5;
  FUN_100116ec(1);
  memw();
  if ((*puVar1 & DAT_10005e80) != 0) {
    local_30 = DAT_1000605c;
  }
  FUN_100116ec(1);
  memw();
  memw();
  *puVar1 = *puVar1 & uVar2;
  FUN_100116ec(2);
  return local_30;
}


