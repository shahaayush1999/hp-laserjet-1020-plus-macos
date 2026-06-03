/*
Function: 1001788c hp1020_threadx_diag_1001788c
Strings:
- descriptor:System Timer Thread
*/


void hp1020_threadx_diag_1001788c(int param_1,uint param_2)

{
  int *piVar1;
  int *piVar2;
  undefined *puVar3;
  undefined *puVar4;
  undefined4 uVar5;
  uint *puVar6;
  int iVar7;
  int iVar8;
  code *pcVar9;
  uint uVar10;
  undefined1 uVar11;
  uint *puStack_30;
  undefined4 auStack_2c [11];
  
  puVar3 = PTR_DAT_10006adc;
  uVar10 = 0;
  if (param_1 != DAT_10006af4) {
    return;
  }
  auStack_2c[0] = 0;
  do {
    uVar5 = rsil(1);
    puVar6 = (uint *)**(int **)puVar3;
    if (puVar6 != (uint *)0x0) {
      puVar6[6] = (uint)&puStack_30;
    }
    puVar4 = PTR_DAT_10006ae0;
    **(undefined4 **)puVar3 = 0;
    iVar7 = *(int *)puVar3;
    iVar8 = *(int *)puVar4;
    *(int *)puVar3 = iVar7 + 4;
    if (iVar7 + 4 == iVar8) {
      *(undefined4 *)puVar3 = *(undefined4 *)PTR_DAT_10006ad8;
    }
    *(undefined4 *)PTR_DAT_10006ad0 = 0;
    wsr((char)uVar10,uVar5);
    rsync();
    uVar5 = rsil(1);
    piVar1 = (int *)PTR_DAT_10006a9c;
    piVar2 = (int *)PTR_DAT_10006ac0;
    while (uVar11 = (undefined1)uVar10, PTR_DAT_10006a9c = (undefined *)piVar1,
          PTR_DAT_10006ac0 = (undefined *)piVar2, puVar6 != (uint *)0x0) {
      if (puVar6 == (uint *)puVar6[4]) {
        puStack_30 = (uint *)0x0;
      }
      else {
        ((uint *)puVar6[4])[5] = puVar6[5];
        *(uint *)(puVar6[5] + 0x10) = puVar6[4];
        *(uint ***)(puVar6[4] + 0x18) = &puStack_30;
        puStack_30 = (uint *)puVar6[4];
      }
      if (*puVar6 < 0x21) {
        pcVar9 = (code *)puVar6[2];
        param_2 = puVar6[3];
        *puVar6 = puVar6[1];
        if (puVar6[1] != 0) goto LAB_1001791a;
        puVar6[6] = 0;
      }
      else {
        *puVar6 = *puVar6 - 0x20;
        pcVar9 = (code *)0x0;
LAB_1001791a:
        puVar6[6] = (uint)auStack_2c;
        puVar6[4] = (uint)puVar6;
      }
      wsr(uVar11,uVar5);
      rsync();
      if (pcVar9 != (code *)0x0) {
        uVar10 = uVar10 & 0xffffcfff;
        (*pcVar9)(param_2);
      }
      uVar5 = rsil(1);
      if ((undefined4 *)puVar6[6] == auStack_2c) {
        puVar6[6] = 0;
        uVar10 = uVar10 & 0xffffcfff;
        FUN_1001a590(puVar6);
      }
      wsr((char)uVar10,uVar5);
      rsync();
      uVar5 = rsil(1);
      puVar6 = puStack_30;
      piVar1 = (int *)PTR_DAT_10006a9c;
      piVar2 = (int *)PTR_DAT_10006ac0;
    }
    if (*(int *)PTR_DAT_10006ad0 == 0) {
      iVar8 = *piVar1;
      *(undefined4 *)(iVar8 + 0x30) = 3;
      iVar7 = *piVar2;
      *(undefined4 *)(iVar8 + 0x38) = 1;
      *piVar2 = iVar7 + 1;
      wsr(uVar11,uVar5);
      rsync();
      uVar10 = uVar10 & 0xffffcfff;
      puStack_30 = puVar6;
      FUN_100176c8(*piVar1);
    }
    else {
      wsr(uVar11,uVar5);
      rsync();
    }
  } while( true );
}


