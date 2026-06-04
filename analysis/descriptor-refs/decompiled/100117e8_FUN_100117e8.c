/* Function: 100117e8 FUN_100117e8 */


int FUN_100117e8(byte *param_1,short param_2,short param_3,char param_4)

{
  byte bVar1;
  uint *puVar2;
  int iVar3;
  uint uVar4;
  int iVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  byte *local_50;
  int iStack_2c;
  
  iStack_2c = 0;
  iVar3 = FUN_10011ba0();
  puVar2 = DAT_100064cc;
  local_50 = param_1;
  if (iVar3 == DAT_1000605c) {
    return iVar3;
  }
  while (((param_3 != 0 && (iStack_2c = FUN_10011c44(0xa0,param_2), iStack_2c == 0)) &&
         (iStack_2c = FUN_10011d2c(param_2), iStack_2c == 0))) {
    if (param_4 == '\x01') {
      iStack_2c = FUN_10011c44(0xa1,param_2);
      if ((iStack_2c != 0) || (param_3 == 0)) break;
      do {
        memw();
        uVar6 = 0x80;
        uVar4 = 0;
        uVar7 = 0;
        memw();
        *DAT_100064c4 = *DAT_100064c4 & DAT_100064c8;
        do {
          memw();
          uVar7 = uVar7 + 1;
          memw();
          *puVar2 = *puVar2 | DAT_100064d0;
          FUN_100116ec(1);
          memw();
          uVar8 = uVar4 | uVar6;
          uVar6 = uVar6 >> 1;
          if ((*puVar2 & DAT_10005e80) != 0) {
            uVar4 = uVar8;
          }
          FUN_100116ec(1);
          memw();
          memw();
          *puVar2 = *puVar2 & DAT_100064d4;
          FUN_100116ec(2);
        } while (uVar7 < 8);
        *local_50 = (byte)uVar4;
        memw();
        local_50 = local_50 + 1;
        param_3 = param_3 + -1;
        memw();
        *DAT_100064c4 = *DAT_100064c4 | DAT_10005e80;
        if (param_3 == 0) {
          memw();
          uVar4 = *puVar2 | DAT_10005e80;
        }
        else {
          memw();
          uVar4 = *puVar2 & DAT_100064c8;
        }
        memw();
        *puVar2 = uVar4;
        memw();
        memw();
        *puVar2 = *puVar2 | DAT_100064d0;
        FUN_100116ec(2);
        memw();
        memw();
        *puVar2 = *puVar2 & DAT_100064d4;
        FUN_100116ec(2);
      } while (param_3 != 0);
    }
    else {
      uVar4 = FUN_1001b618(param_2,*PTR_DAT_100064c0);
      while ((param_3 != 0 && (uVar4 < (byte)*PTR_DAT_100064c0))) {
        bVar1 = *local_50;
        memw();
        local_50 = local_50 + 1;
        uVar6 = 0x80;
        uVar7 = 0;
        memw();
        *DAT_100064c4 = *DAT_100064c4 | DAT_10005e80;
        do {
          if ((bVar1 & uVar6) == 0) {
            memw();
            uVar8 = *puVar2 & DAT_100064c8;
          }
          else {
            memw();
            uVar8 = *puVar2 | DAT_10005e80;
          }
          memw();
          *puVar2 = uVar8;
          FUN_100116ec(1);
          uVar6 = uVar6 >> 1;
          memw();
          uVar7 = uVar7 + 1;
          memw();
          *puVar2 = *puVar2 | DAT_100064d0;
          FUN_100116ec(2);
          memw();
          memw();
          *puVar2 = *puVar2 & DAT_100064d4;
          FUN_100116ec(1);
        } while (uVar7 < 8);
        memw();
        memw();
        *DAT_100064c4 = *DAT_100064c4 & DAT_100064c8;
        memw();
        memw();
        *puVar2 = *puVar2 | DAT_100064d0;
        FUN_100116ec(1);
        memw();
        if ((*puVar2 & DAT_10005e80) != 0) goto LAB_10011808;
        FUN_100116ec(1);
        param_3 = param_3 + -1;
        memw();
        param_2 = param_2 + 1;
        uVar4 = uVar4 + 1;
        memw();
        *puVar2 = *puVar2 & DAT_100064d4;
        FUN_100116ec(1);
      }
      FUN_10011aa0();
      iVar3 = FUN_100175cc();
      do {
        iVar5 = FUN_10011c44(0xa0,0);
        if (iVar5 != DAT_1000605c) break;
        iVar5 = FUN_100175cc();
      } while ((uint)(iVar5 - iVar3) < 500);
      iVar5 = FUN_100175cc();
      if (500 < (uint)(iVar5 - iVar3)) {
LAB_10011808:
        FUN_10011aa0();
        return DAT_1000605c;
      }
    }
  }
  FUN_10011aa0();
  return iStack_2c;
}


