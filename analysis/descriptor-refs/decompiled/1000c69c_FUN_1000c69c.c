/* Function: 1000c69c FUN_1000c69c */


void FUN_1000c69c(char param_1,char *param_2,undefined4 param_3)

{
  undefined2 uVar1;
  uint uVar2;
  undefined *puVar3;
  int iVar4;
  undefined4 uVar5;
  ushort uVar6;
  int *piVar7;
  int iVar8;
  undefined *puVar9;
  undefined *puVar10;
  undefined1 in_b4;
  undefined auStack_30 [48];
  
  puVar9 = PTR_DAT_100060d4;
  uVar1 = *(undefined2 *)(PTR_DAT_100060dc + 4);
  *(undefined4 *)PTR_DAT_100060d4 = *(undefined4 *)PTR_DAT_100060dc;
  *(undefined2 *)(puVar9 + 4) = uVar1;
  puVar10 = PTR_s_INQUIRE_10006260;
  if (param_1 != '\0') {
    puVar10 = PTR_s_DINQUIRE_1000625c;
  }
  FUN_1001b544(puVar9,puVar10);
  puVar9 = PTR_DAT_100060d4;
  if ((param_2 != (char *)0x0) && (*param_2 != '\0')) {
    FUN_1001b544(PTR_DAT_100060d4,PTR_s_LPARM__10006238);
    FUN_1001b544(puVar9,PTR_DAT_10006144);
    FUN_1001b544(puVar9,PTR_DAT_100060e4);
  }
  puVar9 = PTR_DAT_100060d4;
  FUN_1001b544(PTR_DAT_100060d4,param_3);
  FUN_1001b544(puVar9,PTR_DAT_100060ec);
  uVar2 = FUN_1000b808(param_2,param_3);
  puVar10 = PTR_DAT_10006148;
  puVar3 = PTR_DAT_10006254;
  if (1 < uVar2) {
    uVar6 = 0;
    do {
      iVar4 = FUN_1001684c(param_3,*(undefined4 *)(puVar10 + (uint)uVar6 * 0x24 + 4));
      puVar9 = PTR_DAT_100060d4;
      if (iVar4 == 0) break;
      uVar6 = uVar6 + 1;
    } while (uVar6 < 0x14);
    if (uVar2 == 3) {
      iVar4 = FUN_1000b870(param_1,uVar6);
      if ((bool)in_b4) {
        FUN_1001b544(PTR_DAT_100060d4,PTR_DAT_10006264);
        iVar4 = -iVar4;
      }
      piVar7 = (int *)(puVar10 + (uint)uVar6 * 0x24);
      iVar8 = piVar7[5];
      if (iVar8 == 6) {
        if ((*piVar7 == 4) && (iVar4 == 0)) goto LAB_1000c80a;
        FUN_1000ae3c(auStack_30,iVar4);
        puVar9 = PTR_DAT_100060d4;
        puVar3 = auStack_30;
      }
      else {
        if (iVar8 != 7) goto LAB_1000c80a;
        uVar5 = FUN_1001b5b8(iVar4,100);
        FUN_1000ae3c(auStack_30,uVar5);
        puVar9 = PTR_DAT_100060d4;
        FUN_1001b544(PTR_DAT_100060d4,auStack_30);
        FUN_1001b544(puVar9,PTR_DAT_1000623c);
        iVar4 = FUN_1001b618(iVar4,100);
        if (iVar4 < 10) {
          FUN_1001b544(puVar9,PTR_DAT_10006240);
        }
        FUN_1000ae3c(auStack_30,iVar4);
        puVar3 = auStack_30;
      }
    }
    else {
      uVar5 = FUN_1000b870(param_1,uVar6);
      puVar3 = (undefined *)FUN_1000b9d8(param_3,uVar5);
    }
  }
  FUN_1001b544(puVar9,puVar3);
LAB_1000c80a:
  puVar9 = PTR_DAT_100060d4;
  FUN_1001b544(PTR_DAT_100060d4,PTR_DAT_100060ec);
  FUN_1001b544(puVar9,PTR_DAT_100060f8);
  iVar4 = FUN_100169d4(puVar9);
  uVar5 = FUN_1000dc00(iVar4 + 1);
  FUN_1001693c(uVar5,puVar9);
  FUN_1000cd44(uVar5,1);
  FUN_1000b1c4();
  return;
}


