/* Function: 10011d2c FUN_10011d2c */


void FUN_10011d2c(ushort param_1)

{
  uint *puVar1;
  uint *puVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  
  puVar1 = DAT_100064c4;
  uVar4 = 8;
  iVar3 = 0;
  uVar5 = 0x80;
  if (*PTR_DAT_100064bc == '\x02') {
    uVar4 = 0x10;
    uVar5 = DAT_10005e6c;
  }
  memw();
  uVar6 = 0;
  memw();
  *DAT_100064c4 = *DAT_100064c4 | DAT_10005e80;
  puVar2 = DAT_100064cc;
  if (uVar4 != 0) {
    do {
      FUN_100116ec(1);
      if ((uVar5 & param_1) == 0) {
        memw();
        uVar7 = *puVar2 & DAT_100064c8;
      }
      else {
        memw();
        uVar7 = *puVar2 | DAT_10005e80;
      }
      memw();
      *puVar2 = uVar7;
      FUN_100116ec(1);
      memw();
      memw();
      *puVar2 = *puVar2 | DAT_100064d0;
      FUN_100116ec(2);
      memw();
      uVar5 = uVar5 >> 1;
      memw();
      *puVar2 = *puVar2 & DAT_100064d4;
      if ((uVar6 == 7) || (uVar6 == 0xf)) {
        FUN_100116ec(2);
        memw();
        memw();
        *puVar1 = *puVar1 & DAT_100064c8;
        memw();
        memw();
        *puVar2 = *puVar2 | DAT_100064d0;
        FUN_100116ec(1);
        memw();
        if ((*puVar2 & DAT_10005e80) != 0) {
          iVar3 = DAT_1000605c;
        }
        FUN_100116ec(1);
        memw();
        memw();
        *puVar2 = *puVar2 & DAT_100064d4;
        FUN_100116ec(2);
        if (iVar3 != 0) {
          return;
        }
        memw();
        memw();
        *puVar1 = *puVar1 | DAT_10005e80;
      }
      uVar6 = uVar6 + 1;
    } while (uVar6 < uVar4);
  }
  return;
}


