/* Function: 1000c230 FUN_1000c230 */


undefined4 FUN_1000c230(undefined4 param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  uint uVar3;
  undefined *puVar4;
  int iVar5;
  uint uVar6;
  undefined *puVar7;
  undefined1 *puVar8;
  undefined1 auStack_50 [16];
  uint uStack_40;
  uint uStack_3c;
  uint *puStack_38;
  int *piStack_34;
  undefined4 *puStack_30;
  
  uStack_40 = 0;
  puStack_38 = (uint *)(PTR_DAT_10006148 + 0x10);
  piStack_34 = (int *)(PTR_DAT_10006148 + 0x14);
  puStack_30 = (undefined4 *)(PTR_DAT_10006148 + 4);
  puVar4 = PTR_DAT_10006148;
  do {
    if (puVar4[0xc] == '\x01') {
      FUN_1001b544(param_1,PTR_s_LPARM__10006238);
      FUN_1001b544(param_1,PTR_DAT_10006144);
      FUN_1001b544(param_1,PTR_DAT_100060e4);
    }
    FUN_1001b544(param_1,*puStack_30);
    FUN_1001b544(param_1,PTR_DAT_100060f4);
    if (*(int *)(puVar4 + 8) == 3) {
      uVar1 = FUN_1000b870(0,uStack_40 & 0xffff);
      if (*piStack_34 == 6) {
        FUN_1000ae3c(auStack_50,uVar1);
        puVar8 = auStack_50;
        goto LAB_1000c321;
      }
      if (*piStack_34 == 7) {
        uVar2 = FUN_1001b668(uVar1,100);
        FUN_1000ae3c(auStack_50,uVar2);
        FUN_1001b544(param_1,auStack_50);
        FUN_1001b544(param_1,PTR_DAT_1000623c);
        uVar6 = FUN_1001b6b0(uVar1,100);
        if (uVar6 < 10) {
          FUN_1001b544(param_1,PTR_DAT_10006240);
        }
        FUN_1000ae3c(auStack_50,uVar6);
        puVar8 = auStack_50;
        goto LAB_1000c321;
      }
    }
    else {
      uVar1 = FUN_1000b870(0,uStack_40 & 0xffff);
      puVar8 = (undefined1 *)FUN_1000b9d8(*puStack_30,uVar1);
LAB_1000c321:
      FUN_1001b544(param_1,puVar8);
    }
    uVar6 = *puStack_38;
    if (uVar6 == 0) {
      FUN_1001b544(param_1,PTR_s__2_RANGE__1000622c);
      FUN_1001b544(param_1,PTR_DAT_100060ec);
      FUN_1001b544(param_1,PTR_DAT_1000615c);
      uVar6 = *(uint *)(puVar4 + 0x18);
      if (*piStack_34 == 6) {
LAB_1000c3a1:
        FUN_1000ae3c(auStack_50,uVar6);
        FUN_1001b544(param_1,auStack_50);
      }
      else if (*piStack_34 == 7) {
        uVar1 = FUN_1001b668(uVar6,100);
        FUN_1000ae3c(auStack_50,uVar1);
        FUN_1001b544(param_1,auStack_50);
        FUN_1001b544(param_1,PTR_DAT_1000623c);
        uVar6 = FUN_1001b6b0(uVar6,100);
        if (uVar6 < 10) {
          FUN_1001b544(param_1,PTR_DAT_10006240);
        }
        goto LAB_1000c3a1;
      }
      FUN_1001b544(param_1,PTR_DAT_100060ec);
      FUN_1001b544(param_1,PTR_DAT_1000615c);
      uVar6 = *(uint *)(puVar4 + 0x1c);
      if (*piStack_34 == 6) {
LAB_1000c41d:
        FUN_1000ae3c(auStack_50,uVar6);
        FUN_1001b544(param_1,auStack_50);
      }
      else if (*piStack_34 == 7) {
        uVar1 = FUN_1001b668(uVar6,100);
        FUN_1000ae3c(auStack_50,uVar1);
        FUN_1001b544(param_1,auStack_50);
        FUN_1001b544(param_1,PTR_DAT_1000623c);
        uVar6 = FUN_1001b6b0(uVar6,100);
        if (uVar6 < 10) {
          FUN_1001b544(param_1,PTR_DAT_10006240);
        }
        goto LAB_1000c41d;
      }
      FUN_1001b544(param_1,PTR_DAT_100060ec);
    }
    else {
      FUN_1001b544(param_1,PTR_DAT_10006244);
      FUN_1000ae3c(auStack_50,uVar6);
      FUN_1001b544(param_1,auStack_50);
      puVar7 = PTR_s_ENUMERATED__100061a8;
      if (puVar4[0xd] != '\0') {
        puVar7 = DAT_10006248;
      }
      FUN_1001b544(param_1,puVar7);
      FUN_1001b544(param_1,PTR_DAT_100060ec);
      uVar6 = 0;
      if (*puStack_38 != 0) {
        iVar5 = 0;
        uStack_3c = *puStack_38;
        do {
          FUN_1001b544(param_1,PTR_DAT_1000615c);
          if (*(int *)(puVar4 + 8) == 3) {
            uVar1 = *(undefined4 *)(iVar5 + *(int *)(puVar4 + 0x20) + 4);
            if (*(int *)(puVar4 + 0x14) == 6) {
              FUN_1000ae3c(auStack_50,uVar1);
              puVar8 = auStack_50;
              goto LAB_1000c51d;
            }
            if (*(int *)(puVar4 + 0x14) == 7) {
              uVar2 = FUN_1001b668(uVar1,100);
              FUN_1000ae3c(auStack_50,uVar2);
              FUN_1001b544(param_1,auStack_50);
              FUN_1001b544(param_1,PTR_DAT_1000623c);
              uVar3 = FUN_1001b6b0(uVar1,100);
              if (uVar3 < 10) {
                FUN_1001b544(param_1,PTR_DAT_10006240);
              }
              FUN_1000ae3c(auStack_50,uVar3);
              puVar8 = auStack_50;
              goto LAB_1000c51d;
            }
          }
          else {
            puVar8 = *(undefined1 **)(iVar5 + *(int *)(puVar4 + 0x20));
LAB_1000c51d:
            FUN_1001b544(param_1,puVar8);
          }
          iVar5 = iVar5 + 8;
          FUN_1001b544(param_1,PTR_DAT_100060ec);
          uVar6 = uVar6 + 1;
        } while (uVar6 < uStack_3c);
      }
    }
    puStack_38 = puStack_38 + 9;
    piStack_34 = piStack_34 + 9;
    puVar4 = puVar4 + 0x24;
    puStack_30 = puStack_30 + 9;
    uStack_40 = uStack_40 + 1;
    if (10 < uStack_40) {
      return 0;
    }
  } while( true );
}


